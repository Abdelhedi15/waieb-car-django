from rest_framework import serializers
from .models import Paiement, Avance

class PaiementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paiement
        fields = '__all__'

class AvanceSerializer(serializers.ModelSerializer):
    montant_total = serializers.ReadOnlyField()
    class Meta:
        model = Avance
        fields = '__all__'