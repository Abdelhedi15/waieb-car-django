from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    points_gagnes      = serializers.ReadOnlyField()
    points_disponibles = serializers.ReadOnlyField()

    class Meta:
        model  = User
        fields = [
            'id', 'username', 'email', 'nom', 'prenom', 'role', 'telephone',
            # ── Wallet / Fidélité
            'points_utilises', 'solde_wallet',
            'points_gagnes', 'points_disponibles',
        ]
        # points_utilises est éditable via PATCH /api/auth/me/
        read_only_fields = ['points_gagnes', 'points_disponibles']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model  = User
        fields = ['username', 'email', 'password', 'nom', 'prenom', 'role']

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user