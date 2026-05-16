# -*- coding: utf-8 -*-
import random
import string
import threading
import mailjet_rest
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.conf import settings
from .models import User
from .serializers import UserSerializer


def _send_email(to, subject, body):
    """Send email via Mailjet API in background thread."""
    def _run():
        try:
            client = mailjet_rest.Client(
                auth=(settings.MAILJET_API_KEY, settings.MAILJET_SECRET_KEY),
                version='v3.1'
            )
            data = {
                'Messages': [{
                    'From': {
                        'Email': settings.MAILJET_FROM_EMAIL,
                        'Name': settings.MAILJET_FROM_NAME,
                    },
                    'To': [{'Email': to}],
                    'Subject': subject,
                    'TextPart': body,
                }]
            }
            result = client.send.create(data=data)
            print(f'[mailjet] Sent to {to} - status {result.status_code}')
        except Exception as e:
            print(f'[mailjet] Error: {e}')
    threading.Thread(target=_run, daemon=True).start()


class LoginView(APIView):
    permission_classes = []

    def post(self, request):
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')

        user = authenticate(username=username, password=password)
        if not user:
            try:
                u = User.objects.get(email__iexact=username)
                user = authenticate(username=u.username, password=password)
            except User.DoesNotExist:
                pass

        if user:
            refresh = RefreshToken.for_user(user)
            client_id = None
            try:
                client_id = user.client_profile.id
            except Exception:
                pass
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id': user.id,
                    'client_id': client_id,
                    'username': user.username,
                    'nom': user.nom,
                    'prenom': user.prenom,
                    'role': user.role,
                    'email': user.email,
                }
            })
        return Response({'detail': 'Identifiants incorrects'}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    def post(self, request):
        return Response({'message': 'Deconnecte'})


class MeView(APIView):
    def get(self, request):
        user = request.user
        client_id = None
        try:
            client_id = user.client_profile.id
        except Exception:
            pass
        return Response({
            'id': user.id,
            'client_id': client_id,
            'username': user.username,
            'nom': user.nom,
            'prenom': user.prenom,
            'role': user.role,
            'email': user.email,
            'telephone': getattr(user, 'telephone', ''),
        })


class ForgotPasswordView(APIView):
    permission_classes = []

    def post(self, request):
        email = request.data.get('email', '').strip()
        if not email:
            return Response({'detail': 'Email requis'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            # On retourne 200 même si email inexistant (sécurité)
            return Response({'detail': 'Mot de passe temporaire envoye par email.'}, status=status.HTTP_200_OK)

        new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        user.set_password(new_password)
        user.save()

        _send_email(
            to=email,
            subject='Reinitialisation mot de passe - Waieb Car Rent',
            body=(
                f"Bonjour {user.prenom} {user.nom},\n\n"
                f"Votre nouveau mot de passe temporaire :\n\n"
                f"    {new_password}\n\n"
                f"Connectez-vous et changez-le dans votre profil.\n\n"
                f"Cordialement,\nWaieb Car Rent"
            )
        )
        return Response({'detail': 'Mot de passe temporaire envoye par email.'}, status=status.HTTP_200_OK)


class UserListView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [AllowAny()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        password = data.get('password')
        role = data.get('role', 'employee')
        email = data.get('email', '').strip()
        username = data.get('username', email).strip()

        if User.objects.filter(username__iexact=username).exists():
            return Response({'detail': 'Email deja utilise'}, status=status.HTTP_400_BAD_REQUEST)
        if email and User.objects.filter(email__iexact=email).exists():
            return Response({'detail': 'Email deja utilise'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.create_user(
                username=username, password=password,
                nom=data.get('nom', ''), prenom=data.get('prenom', ''),
                email=email, role=role,
            )
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if role == 'client':
            try:
                from rentals.models import Client
                Client.objects.create(
                    user=user, nom=data.get('nom', ''), prenom=data.get('prenom', ''),
                    email=email or None, telephone=data.get('telephone', ''),
                )
                _send_email(
                    to=email,
                    subject='Bienvenue sur Waieb Car Rent !',
                    body=(
                        f"Bonjour {data.get('prenom', '')} {data.get('nom', '')},\n\n"
                        f"Votre compte a ete cree avec succes.\n"
                        f"Email: {email}\n\n"
                        f"Bonne location !\nWaieb Car Rent"
                    )
                )
            except Exception as e:
                print(f'[UserListView] Client creation error: {e}')

        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        data = request.data.copy()
        password = data.pop('password', None)
        for key, value in data.items():
            if hasattr(user, key) and key not in ['id']:
                setattr(user, key, value)
        if password:
            user.set_password(password)
        user.save()
        return Response(UserSerializer(user).data)