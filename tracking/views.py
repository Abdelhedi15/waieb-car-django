# -*- coding: utf-8 -*-
import os
import threading
import requests as req_lib
import resend
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from .models import ClientLocation, ChatMessage
from rentals.models import Client


def _send_email_mailjet(to_email, to_name, subject, body):
    """Send email via Mailjet for client notifications."""
    def _run():
        try:
            from mailjet_rest import Client as MJClient
            mj = MJClient(auth=(settings.MAILJET_API_KEY, settings.MAILJET_SECRET_KEY), version='v3.1')
            data = {
                'Messages': [{
                    'From': {'Email': settings.MAILJET_FROM_EMAIL, 'Name': settings.MAILJET_FROM_NAME},
                    'To': [{'Email': to_email, 'Name': to_name}],
                    'Subject': subject,
                    'TextPart': body,
                }]
            }
            result = mj.send.create(data=data)
            print(f'[mailjet] Sent to {to_email} status={result.status_code}')
        except Exception as e:
            print(f'[mailjet] Error: {e}')
    threading.Thread(target=_run, daemon=True).start()


def _send_email_resend(to, subject, body):
    """Send via Resend for forgot-password."""
    def _run():
        try:
            resend.api_key = settings.RESEND_API_KEY
            resend.Emails.send({
                "from": settings.DEFAULT_FROM_EMAIL,
                "to": [to],
                "subject": subject,
                "text": body,
            })
            print(f'[resend] Sent to {to}')
        except Exception as e:
            print(f'[resend] Error: {e}')
    threading.Thread(target=_run, daemon=True).start()


# Keep backward compat
def _send_email(to, subject, body):
    _send_email_resend(to, subject, body)


class UpdateLocationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        lat = request.data.get('latitude')
        lng = request.data.get('longitude')
        is_sharing = request.data.get('is_sharing', True)
        if lat is None or lng is None:
            return Response({'detail': 'latitude and longitude required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            client = request.user.client_profile
        except Exception:
            return Response({'detail': 'Client profile not found'}, status=status.HTTP_404_NOT_FOUND)
        loc, _ = ClientLocation.objects.update_or_create(
            client=client,
            defaults={'latitude': float(lat), 'longitude': float(lng), 'is_sharing': is_sharing}
        )
        return Response({'status': 'ok', 'latitude': loc.latitude, 'longitude': loc.longitude, 'updated_at': loc.updated_at})


class AllLocationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        locations = ClientLocation.objects.filter(is_sharing=True).select_related('client')
        return Response([{
            'client_id': loc.client.id,
            'client_name': f'{loc.client.prenom} {loc.client.nom}',
            'telephone': loc.client.telephone or '',
            'latitude': loc.latitude,
            'longitude': loc.longitude,
            'updated_at': loc.updated_at,
        } for loc in locations])


class StopSharingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            client = request.user.client_profile
            ClientLocation.objects.filter(client=client).update(is_sharing=False)
            return Response({'status': 'stopped'})
        except Exception:
            return Response({'detail': 'error'}, status=status.HTTP_400_BAD_REQUEST)


ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
SYSTEM_PROMPT = """Tu es l'assistant de Waieb Car Rent, une agence de location de voitures a Sfax, Tunisie.
Tu reponds aux questions des clients sur:
- Les vehicules disponibles et leurs prix (a partir de 130 DT/jour)
- Les reservations et le processus de location
- Les documents requis (CIN, permis de conduire)
- Les horaires: Lun-Sam 8h00-19h00
- L'adresse: Rue Taher Sfar, Sfax 3000
- L'acompte: 20% pour 1-3j, 30% pour 4-7j, 40% pour 8-14j, 50% pour 15j+
- Prix saisonniers: +25% juin/sept, +50% juil/aout
- La caution est obligatoire
Reponds toujours en francais, de facon courte et professionnelle."""


def _call_claude(messages):
    try:
        resp = req_lib.post(
            'https://api.anthropic.com/v1/messages',
            headers={'x-api-key': ANTHROPIC_API_KEY, 'anthropic-version': '2023-06-01', 'content-type': 'application/json'},
            json={'model': 'claude-haiku-4-5-20251001', 'max_tokens': 300, 'system': SYSTEM_PROMPT, 'messages': messages},
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json()['content'][0]['text']
        return "Desolee, je ne peux pas repondre pour le moment. Appelez le +216 74 000 001."
    except Exception as e:
        print(f'[claude] error: {e}')
        return "Service momentanement indisponible. Contactez-nous au +216 74 000 001."


class ChatView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            client = request.user.client_profile
        except Exception:
            return Response([], status=200)
        messages = ChatMessage.objects.filter(client=client).order_by('created_at')
        return Response([{'id': m.id, 'sender': m.sender, 'message': m.message, 'created_at': m.created_at, 'is_read': m.is_read} for m in messages])

    def post(self, request):
        text = request.data.get('message', '').strip()
        if not text:
            return Response({'detail': 'message required'}, status=400)
        try:
            client = request.user.client_profile
        except Exception:
            return Response({'detail': 'Client profile not found'}, status=404)

        ChatMessage.objects.create(client=client, sender='client', message=text)

        history = list(reversed(ChatMessage.objects.filter(client=client).order_by('-created_at')[:10]))
        claude_messages = []
        for h in history:
            if h.sender == 'client':
                claude_messages.append({'role': 'user', 'content': h.message})
            elif h.sender in ['bot', 'employee']:
                claude_messages.append({'role': 'assistant', 'content': h.message})

        bot_reply = _call_claude(claude_messages)
        bot_msg = ChatMessage.objects.create(client=client, sender='bot', message=bot_reply)
        return Response({'id': bot_msg.id, 'sender': 'bot', 'message': bot_reply, 'created_at': bot_msg.created_at})


class EmployeeChatView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        clients = Client.objects.filter(chat_messages__isnull=False).distinct()
        result = []
        for client in clients:
            last_msg = ChatMessage.objects.filter(client=client).order_by('-created_at').first()
            unread = ChatMessage.objects.filter(client=client, sender='client', is_read=False).count()
            result.append({
                'client_id': client.id, 'client_name': f'{client.prenom} {client.nom}',
                'telephone': client.telephone or '',
                'last_message': last_msg.message if last_msg else '',
                'last_message_time': last_msg.created_at if last_msg else None,
                'unread_count': unread,
            })
        return Response(result)

    def post(self, request):
        client_id = request.data.get('client_id')
        text = request.data.get('message', '').strip()
        if not client_id or not text:
            return Response({'detail': 'client_id and message required'}, status=400)
        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return Response({'detail': 'Client not found'}, status=404)
        ChatMessage.objects.filter(client=client, sender='client', is_read=False).update(is_read=True)
        msg = ChatMessage.objects.create(client=client, sender='employee', message=text)
        return Response({'id': msg.id, 'sender': 'employee', 'message': text, 'created_at': msg.created_at})


class ClientChatHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, client_id):
        messages = ChatMessage.objects.filter(client_id=client_id).order_by('created_at')
        ChatMessage.objects.filter(client_id=client_id, sender='client', is_read=False).update(is_read=True)
        return Response([{'id': m.id, 'sender': m.sender, 'message': m.message, 'created_at': m.created_at} for m in messages])