from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User
from .serializers import UserSerializer


class LoginView(APIView):
    permission_classes = []

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'access':  str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id':       user.id,
                    'username': user.username,
                    'nom':      user.nom,
                    'prenom':   user.prenom,
                    'role':     user.role,
                    'email':    user.email,
                }
            })
        return Response(
            {'detail': 'Identifiants incorrects'},
            status=status.HTTP_401_UNAUTHORIZED
        )


class LogoutView(APIView):
    def post(self, request):
        return Response({'message': 'Déconnecté'})


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

        # Check email uniqueness first
        email = data.get('email', '')
        username = data.get('username', email)
        if User.objects.filter(username=username).exists():
            return Response(
                {'username': ['Cet email est déjà utilisé.']},
                status=status.HTTP_400_BAD_REQUEST
            )
        if email and User.objects.filter(email=email).exists():
            return Response(
                {'email': ['Cet email est déjà utilisé.']},
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