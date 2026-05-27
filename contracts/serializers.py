from rest_framework import serializers
from .models import Contrat


class ContratSerializer(serializers.ModelSerializer):
    # Champs enrichis pour l'affichage Flutter
    client_nom = serializers.SerializerMethodField()
    date_debut = serializers.SerializerMethodField()
    date_fin = serializers.SerializerMethodField()

    class Meta:
        model = Contrat
        fields = [
            'id',
            'numero',
            'reservation',
            'date_contrat',
            'contenu',
            'statut',        # ✅ champ statut exposé
            'client_nom',    # ✅ nom du client
            'date_debut',    # ✅ date début de la résa
            'date_fin',      # ✅ date fin de la résa
            'created_at',
        ]
        read_only_fields = ['numero', 'created_at']

    def get_client_nom(self, obj):
        try:
            r = obj.reservation
            if r.client:
                return f"{r.client.prenom} {r.client.nom}".strip()
            return ''
        except Exception:
            return ''

    def get_date_debut(self, obj):
        try:
            return str(obj.reservation.date_debut)
        except Exception:
            return ''

    def get_date_fin(self, obj):
        try:
            return str(obj.reservation.date_fin)
        except Exception:
            return ''