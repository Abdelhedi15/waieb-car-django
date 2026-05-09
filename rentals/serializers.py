from rest_framework import serializers
from .models import Client, Reservation
from vehicles.models import Vehicle

class VehicleNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = [
            'id', 'marque', 'modele', 'immatriculation',
            'annee', 'couleur', 'prix_journalier',
            'prix_haute_saison', 'prix_tres_haute_saison',
            'statut', 'type_carburant', 'nombre_places',
            'kilometrage', 'etat_carrosserie', 'photo',
        ]

class ClientSerializer(serializers.ModelSerializer):
    nombre_reservations     = serializers.SerializerMethodField()
    montant_total_depense   = serializers.SerializerMethodField()
    nombre_accidents        = serializers.SerializerMethodField()
    date_premiere_location  = serializers.SerializerMethodField()

    class Meta:
        model  = Client
        fields = '__all__'

    def get_nombre_reservations(self, obj):
        return obj.reservations.filter(statut__in=['confirmée','terminée']).count()

    def get_montant_total_depense(self, obj):
        from django.db.models import Sum
        result = obj.reservations.filter(
            statut__in=['confirmée','terminée']
        ).aggregate(Sum('montant_total'))
        return float(result['montant_total__sum'] or 0)

    def get_nombre_accidents(self, obj):
        return obj.reservations.filter(a_accident=True).count()

    def get_date_premiere_location(self, obj):
        first = obj.reservations.order_by('date_debut').first()
        return first.date_debut if first else None

class ClientNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Client
        fields = ['id', 'nom', 'prenom', 'cin', 'telephone', 'email']

class ReservationSerializer(serializers.ModelSerializer):
    # ── Extra read-only fields for Flutter/React display
    vehicle_details  = VehicleNestedSerializer(source='vehicle', read_only=True)
    client_details   = ClientNestedSerializer(source='client',  read_only=True)
    vehicle_marque   = serializers.CharField(source='vehicle.marque',        read_only=True, default='')
    vehicle_modele   = serializers.CharField(source='vehicle.modele',        read_only=True, default='')
    vehicle_image    = serializers.SerializerMethodField()
    client_nom       = serializers.SerializerMethodField()
    client_prenom    = serializers.SerializerMethodField()

    class Meta:
        model  = Reservation
        fields = '__all__'

    def get_vehicle_image(self, obj):
        request = self.context.get('request')
        if obj.vehicle and obj.vehicle.photo:
            if request:
                return request.build_absolute_uri(obj.vehicle.photo.url)
            return f"http://localhost:8000{obj.vehicle.photo.url}"
        return ''

    def get_client_nom(self, obj):
        if obj.client:
            return f"{obj.client.prenom} {obj.client.nom}"
        return ''

    def get_client_prenom(self, obj):
        return obj.client.prenom if obj.client else ''

class ReservationDetailSerializer(serializers.ModelSerializer):
    client       = ClientSerializer(read_only=True)
    vehicle_info = serializers.SerializerMethodField()

    class Meta:
        model  = Reservation
        fields = '__all__'

    def get_vehicle_info(self, obj):
        return f"{obj.vehicle.marque} {obj.vehicle.modele} - {obj.vehicle.immatriculation}"