# -*- coding: utf-8 -*-
import os
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.conf import settings
from .models import ClientLocation, ChatMessage
from rentals.models import Client


class UpdateLocationView(APIView):
    """Client sends their GPS position."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        lat = request.data.get('latitude')
        lng = request.data.get('longitude')
        is_sharing = request.data.get('is_sharing', True)

        if lat is None or lng is None:
            return Response({'detail': 'latitude and longitude required'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            client = request.user.client_profile
        except Exception:
            return Response({'detail': 'Client profile not found'},
                            status=status.HTTP_404_NOT_FOUND)

        loc, _ = ClientLocation.objects.update_or_create(
            client=client,
            defaults={
                'latitude': float(lat),
                'longitude': float(lng),
                'is_sharing': is_sharing,
            }
        )
        return Response({
            'status': 'ok',
            'latitude': loc.latitude,
            'longitude': loc.longitude,
            'updated_at': loc.updated_at,
        })


class AllLocationsView(APIView):
    """Admin/Employee gets all active client locations."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        locations = ClientLocation.objects.filter(
            is_sharing=True
        ).select_related('client')

        data = []
        for loc in locations:
            data.append({
                'client_id': loc.client.id,
                'client_name': f'{loc.client.prenom} {loc.client.nom}',
                'telephone': loc.client.telephone or '',
                'latitude': loc.latitude,
                'longitude': loc.longitude,
                'updated_at': loc.updated_at,
            })
        return Response(data)


class StopSharingView(APIView):
    """Client stops sharing location."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            client = request.user.client_profile
            ClientLocation.objects.filter(client=client).update(is_sharing=False)
            return Response({'status': 'stopped'})
        except Exception:
            return Response({'detail': 'error'}, status=status.HTTP_400_BAD_REQUEST)


# ─── Chatbot ────────────────────────────────────────────────────────────────

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

SYSTEM_PROMPT = """Tu es l'assistant de Waieb Car Rent, une agence de location de voitures a Sfax, Tunisie.
Tu reponds aux questions des clients sur:
- Les vehicules disponibles et leurs prix
- Les reservations et le processus de location
- Les documents requis (CIN, permis de conduire)
- Les horaires: Lun-Sam 8h00-19h00
- L'adresse: Rue Taher Sfar, Sfax 3000
- L'acompte: 20% pour 1-3j, 30% pour 4-7j, 40% pour 8-14j, 50% pour 15j+
- La caution est obligatoire
Reponds toujours en francais, de facon courte et professionnelle."""


def _call_claude(messages):
    """Call Anthropic Claude API."""
    try:
        resp = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers={
                'x-api-key': ANTHROPIC_API_KEY,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json',
            },
            json={
                'model': 'claude-haiku-4-5-20251001',
                'max_tokens': 300,
                'system': SYSTEM_PROMPT,
                'messages': messages,
            },
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json()['content'][0]['text']
        return "Desolee, je ne peux pas repondre pour le moment. Appelez le +216 71 000 001."
    except Exception as e:
        print(f'[claude] error: {e}')
        return "Desolee, service momentanement indisponible."


class ChatView(APIView):
    """Client sends message, gets AI or employee response."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get chat history for this client."""
        try:
            client = request.user.client_profile
        except Exception:
            return Response([], status=200)

        messages = ChatMessage.objects.filter(client=client).order_by('created_at')
        return Response([{
            'id': m.id,
            'sender': m.sender,
            'message': m.message,
            'created_at': m.created_at,
            'is_read': m.is_read,
        } for m in messages])

    def post(self, request):
        """Client sends a message."""
        text = request.data.get('message', '').strip()
        if not text:
            return Response({'detail': 'message required'}, status=400)

        try:
            client = request.user.client_profile
        except Exception:
            return Response({'detail': 'Client profile not found'}, status=404)

        # Save client message
        ChatMessage.objects.create(
            client=client,
            sender='client',
            message=text,
        )

        # Get conversation history (last 10 messages)
        history = ChatMessage.objects.filter(client=client).order_by('-created_at')[:10]
        history = list(reversed(history))

        claude_messages = []
        for h in history:
            if h.sender == 'client':
                claude_messages.append({'role': 'user', 'content': h.message})
            elif h.sender in ['bot', 'employee']:
                claude_messages.append({'role': 'assistant', 'content': h.message})

        # Get AI response
        bot_reply = _call_claude(claude_messages)

        # Save bot response
        bot_msg = ChatMessage.objects.create(
            client=client,
            sender='bot',
            message=bot_reply,
        )

        return Response({
            'id': bot_msg.id,
            'sender': 'bot',
            'message': bot_reply,
            'created_at': bot_msg.created_at,
        })


class EmployeeChatView(APIView):
    """Employee sees all client chats and can respond."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all clients with their last message."""
        clients_with_msgs = []
        clients = Client.objects.filter(
            chat_messages__isnull=False
        ).distinct()

        for client in clients:
            last_msg = ChatMessage.objects.filter(
                client=client
            ).order_by('-created_at').first()
            unread = ChatMessage.objects.filter(
                client=client,
                sender='client',
                is_read=False
            ).count()

            clients_with_msgs.append({
                'client_id': client.id,
                'client_name': f'{client.prenom} {client.nom}',
                'telephone': client.telephone or '',
                'last_message': last_msg.message if last_msg else '',
                'last_message_time': last_msg.created_at if last_msg else None,
                'unread_count': unread,
            })

        return Response(clients_with_msgs)

    def post(self, request):
        """Employee responds to a client."""
        client_id = request.data.get('client_id')
        text = request.data.get('message', '').strip()

        if not client_id or not text:
            return Response({'detail': 'client_id and message required'}, status=400)

        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return Response({'detail': 'Client not found'}, status=404)

        # Mark client messages as read
        ChatMessage.objects.filter(
            client=client, sender='client', is_read=False
        ).update(is_read=True)

        # Save employee response
        msg = ChatMessage.objects.create(
            client=client,
            sender='employee',
            message=text,
        )

        return Response({
            'id': msg.id,
            'sender': 'employee',
            'message': text,
            'created_at': msg.created_at,
        })


class ClientChatHistoryView(APIView):
    """Employee gets full chat history of a specific client."""
    permission_classes = [IsAuthenticated]

    def get(self, request, client_id):
        messages = ChatMessage.objects.filter(
            client_id=client_id
        ).order_by('created_at')

        # Mark as read
        ChatMessage.objects.filter(
            client_id=client_id, sender='client', is_read=False
        ).update(is_read=True)

        return Response([{
            'id': m.id,
            'sender': m.sender,
            'message': m.message,
            'created_at': m.created_at,
        } for m in messages])