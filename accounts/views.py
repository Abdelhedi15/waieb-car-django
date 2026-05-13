# -*- coding: utf-8 -*-
import random
import string
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from .models import User
from .serializers import UserSerializer


class LoginView(APIView):
    permission_classes = []

    def post(self, request):
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')

        # Try login with username directly
        user = authenticate(username=username, password=password)

        # If failed, try finding user by email then authenticate
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
                'access':  str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id':        user.id,
                    'client_id': client_id,
                    'username':  user.username,
                    'nom':       user.nom,
                    'prenom':    user.prenom,
                    'role':      user.role,
                    'email':     user.email,
                }
            })
        return Response(
            {'detail': 'Identifiants incorrects'},
            status=status.HTTP_401_UNAUTHORIZED
        )


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
            'id':        user.id,
            'client_id': client_id,
            'username':  user.username,
            'nom':       user.nom,
            'prenom':    user.prenom,
            'role':      user.role,
            'email':     user.email,
            'telephone': getattr(user, 'telephone', ''),
        })


class ForgotPasswordView(APIView):
    permission_classes = []

    def post(self, request):
        email = request.data.get('email', '').strip()
        if not email:
            return Response(
                {'detail': 'Email requis'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Find user by email (case insensitive)
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            # Security: don't reveal if email exists or not
            return Response(
                {'detail': 'Si cet email existe, un mot de passe temporaire a ete envoye.'},
                status=status.HTTP_200_OK
            )

        # Generate random 8-char password
        chars = string.ascii_letters + string.digits
        new_password = ''.join(random.choices(chars, k=8))

        # Set new password
        user.set_password(new_password)
        user.save()

        # Send email
        try:
            send_mail(
                subject='Reinitialisation de mot de passe - Waieb Car Rent',
                message=(
                    f"Bonjour {user.prenom} {user.nom},\n\n"
                    f"Votre nouveau mot de passe temporaire est :\n\n"
                    f"    {new_password}\n\n"
                    f"Connectez-vous avec ce mot de passe et changez-le dans votre profil.\n\n"
                    f"Cordialement,\n"
                    f"Waieb Car Rent"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            print(f'[forgot_password] Sent to {email}')
        except Exception as e:
            print(f'[forgot_password] Email error: {e}')
            return Response(
                {'detail': 'Erreur envoi email. Contactez le support.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {'detail': 'Mot de passe temporaire envoye par email.'},
            status=status.HTTP_200_OK
        )


class UserListView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [AllowAny()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        data     = request.data.copy()
        password = data.get('password')
        role     = data.get('role', 'employee')

        email    = data.get('email', '').strip()
        username = data.get('username', email).strip()

        if User.objects.filter(username__iexact=username).exists():
            return Response(
                {'detail': 'Email deja utilise'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if email and User.objects.filter(email__iexact=email).exists():
            return Response(
                {'detail': 'Email deja utilise'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.create_user(
                username=username,
                password=password,
                nom=data.get('nom', ''),
                prenom=data.get('prenom', ''),
                email=email,
                role=role,
            )
        except Exception as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Auto-create Client profile when role is 'client'
        if role == 'client':
            try:
                from rentals.models import Client
                Client.objects.create(
                    user=user,
                    nom=data.get('nom', ''),
                    prenom=data.get('prenom', ''),
                    email=email or None,
                    telephone=data.get('telephone', ''),
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