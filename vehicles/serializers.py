from rest_framework import serializers
from .models import Vehicle

class VehicleSerializer(serializers.ModelSerializer):
    taux_occupation          = serializers.SerializerMethodField()
    nombre_reservations      = serializers.SerializerMethodField()
    nombre_accidents         = serializers.SerializerMethodField()
    duree_flotte_ans         = serializers.ReadOnlyField()   # ✅ Option B
    a_depasse_seuil_vente    = serializers.ReadOnlyField()   # ✅ Option B

    class Meta:
        model = Vehicle
        fields = '__all__'

    def get_taux_occupation(self, obj):
        from rentals.models import Reservation
        return Reservation.objects.filter(vehicle=obj, statut__in=['confirmée', 'terminée']).count()

    def get_nombre_reservations(self, obj):
        return obj.reservations.filter(statut__in=['confirmée', 'terminée']).count()

    def get_nombre_accidents(self, obj):
        return obj.reservations.filter(a_accident=True).count()