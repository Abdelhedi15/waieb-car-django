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
    def _run():
        try:
            client = mailjet_rest.Client(
                auth=(settings.MAILJET_API_KEY, settings.MAILJET_SECRET_KEY),
                version='v3.1'
            )
            data = {
                'Messages': [{
                    'From': {'Email': settings.MAILJET_FROM_EMAIL, 'Name': settings.MAILJET_FROM_NAME},
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

        try:
            points_gagnes = user.points_gagnes
            points_disponibles = user.points_disponibles
        except Exception:
            points_gagnes = 0
            points_disponibles = max(0, -user.points_utilises)

        return Response({
            'id': user.id,
            'client_id': client_id,
            'username': user.username,
            'nom': user.nom,
            'prenom': user.prenom,
            'role': user.role,
            'email': user.email,
            'telephone': getattr(user, 'telephone', ''),
            'points_gagnes': points_gagnes,
            'points_utilises': user.points_utilises,
            'points_disponibles': points_disponibles,
            'solde_wallet': float(user.solde_wallet),
            # ✅ Réductions en attente pour la prochaine réservation
            'reduction_wallet_pending': float(getattr(user, 'reduction_wallet_pending', 0) or 0),
            'reduction_fidelite_pending': float(getattr(user, 'reduction_fidelite_pending', 0) or 0),
            'points_fidelite_pending': int(getattr(user, 'points_fidelite_pending', 0) or 0),
        })

    def patch(self, request):
        """Met à jour points_utilises, solde_wallet et réductions en attente."""
        user = request.user
        data = request.data

        if 'points_utilises' in data:
            user.points_utilises = int(data['points_utilises'])
        if 'solde_wallet' in data:
            user.solde_wallet = float(data['solde_wallet'])

        # ✅ Stocker réductions en attente
        if 'reduction_wallet_pending' in data:
            if hasattr(user, 'reduction_wallet_pending'):
                user.reduction_wallet_pending = float(data['reduction_wallet_pending'])
        if 'reduction_fidelite_pending' in data:
            if hasattr(user, 'reduction_fidelite_pending'):
                user.reduction_fidelite_pending = float(data['reduction_fidelite_pending'])
        if 'points_fidelite_pending' in data:
            if hasattr(user, 'points_fidelite_pending'):
                user.points_fidelite_pending = int(data['points_fidelite_pending'])

        user.save()
        return Response({'status': 'updated'})


class ForgotPasswordView(APIView):
    permission_classes = []

    def post(self, request):
        email = request.data.get('email', '').strip()
        if not email:
            return Response({'detail': 'Email requis'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
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
        role = data.get('role', 'employee')
        email = data.get('email', '').strip()
        username = data.get('username', email).strip()

        auto_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

        if User.objects.filter(username__iexact=username).exists():
            return Response({'detail': 'Nom d\'utilisateur déjà utilisé'}, status=status.HTTP_400_BAD_REQUEST)
        if email and User.objects.filter(email__iexact=email).exists():
            return Response({'detail': 'Email déjà utilisé'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.create_user(
                username=username,
                password=auto_password,
                nom=data.get('nom', ''),
                prenom=data.get('prenom', ''),
                email=email,
                role=role,
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
                        f"Votre compte client a ete cree avec succes.\n"
                        f"Email : {email}\n\n"
                        f"Bonne location !\n\nCordialement,\nWaieb Car Rent"
                    )
                )
            except Exception as e:
                print(f'[UserListView] Client creation error: {e}')

        elif role in ('employee', 'admin') and email:
            role_label = 'employé' if role == 'employee' else 'administrateur'
            app_url = 'l\'application mobile Waieb Car' if role == 'employee' else 'https://waieb-car-react.vercel.app/login'
            _send_email(
                to=email,
                subject=f'Votre compte {role_label} - Waieb Car Rent',
                body=(
                    f"Bonjour {data.get('prenom', '')} {data.get('nom', '')},\n\n"
                    f"Un compte {role_label} a ete cree pour vous sur Waieb Car Rent.\n\n"
                    f"Vos identifiants de connexion :\n"
                    f"  Nom d'utilisateur : {username}\n"
                    f"  Mot de passe      : {auto_password}\n\n"
                    f"Connectez-vous sur : {app_url}\n"
                    f"Changez votre mot de passe apres la premiere connexion.\n\n"
                    f"Cordialement,\nWaieb Car Rent"
                )
            )

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