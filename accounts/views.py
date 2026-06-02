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
        client = None
        try:
            client = user.client_profile
            client_id = client.id
        except Exception:
            pass

        if client:
            points_gagnes              = client.points_gagnes
            points_utilises            = client.points_utilises
            points_disponibles         = client.points_disponibles
            reduction_wallet_pending   = float(client.reduction_wallet_pending or 0)
            reduction_fidelite_pending = float(client.reduction_fidelite_pending or 0)
            points_fidelite_pending    = int(client.points_fidelite_pending or 0)
        else:
            points_gagnes              = 0
            points_utilises            = 0
            points_disponibles         = 0
            reduction_wallet_pending   = 0.0
            reduction_fidelite_pending = 0.0
            points_fidelite_pending    = 0

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
            'points_utilises': points_utilises,
            'points_disponibles': points_disponibles,
            'solde_wallet': float(getattr(user, 'solde_wallet', 0) or 0),
            'reduction_wallet_pending': reduction_wallet_pending,
            'reduction_fidelite_pending': reduction_fidelite_pending,
            'points_fidelite_pending': points_fidelite_pending,
        })

    def patch(self, request):
        user = request.user
        data = request.data

        try:
            client = user.client_profile
            if 'points_utilises' in data:
                client.points_utilises = int(data['points_utilises'])
            if 'reduction_wallet_pending' in data:
                client.reduction_wallet_pending = float(data['reduction_wallet_pending'])
            if 'reduction_fidelite_pending' in data:
                client.reduction_fidelite_pending = float(data['reduction_fidelite_pending'])
            if 'points_fidelite_pending' in data:
                client.points_fidelite_pending = int(data['points_fidelite_pending'])
            client.save()
        except Exception as e:
            print(f'[MeView PATCH] client_profile error: {e}')

        if 'solde_wallet' in data:
            try:
                user.solde_wallet = float(data['solde_wallet'])
                user.save()
            except Exception as e:
                print(f'[MeView PATCH] solde_wallet error: {e}')

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


# ✅ Vue temporaire — initialiser points clients existants
# À SUPPRIMER après utilisation !
class InitPointsView(APIView):
    permission_classes = []

    def get(self, request):
        from rentals.models import Client, Reservation
        updated = []
        for client in Client.objects.all():
            nb = Reservation.objects.filter(
                client=client,
                statut__in=['confirmée', 'confirmee', 'terminée', 'terminee']
            ).count()
            if nb > 0 and client.points_gagnes == 0:
                client.points_gagnes = nb * 100
                client.save(update_fields=['points_gagnes'])
                updated.append({
                    'client': f'{client.prenom} {client.nom}',
                    'points': client.points_gagnes,
                    'reservations': nb,
                })
        return Response({
            'status': 'done',
            'updated': len(updated),
            'details': updated,
        })