from rest_framework import serializers
from .models import Client, Reservation, Favori
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
    nombre_reservations    = serializers.SerializerMethodField()
    montant_total_depense  = serializers.SerializerMethodField()
    nombre_accidents       = serializers.SerializerMethodField()
    date_premiere_location = serializers.SerializerMethodField()

    class Meta:
        model  = Client
        fields = '__all__'

    def get_nombre_reservations(self, obj):
        return obj.reservations.filter(statut__in=['confirmée', 'terminée']).count()

    def get_montant_total_depense(self, obj):
        from django.db.models import Sum
        result = obj.reservations.filter(
            statut__in=['confirmée', 'terminée']
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
    vehicle_details = VehicleNestedSerializer(source='vehicle', read_only=True)
    client_details  = ClientNestedSerializer(source='client',  read_only=True)
    vehicle_marque  = serializers.CharField(source='vehicle.marque', read_only=True, default='')
    vehicle_modele  = serializers.CharField(source='vehicle.modele', read_only=True, default='')
    vehicle_image   = serializers.SerializerMethodField()
    client_nom      = serializers.SerializerMethodField()
    client_prenom   = serializers.SerializerMethodField()

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

    # ✅ VALIDATION CONFLIT — empêche double réservation même véhicule même période
    def validate(self, data):
        vehicle   = data.get('vehicle')   or (self.instance.vehicle   if self.instance else None)
        date_debut = data.get('date_debut') or (self.instance.date_debut if self.instance else None)
        date_fin   = data.get('date_fin')   or (self.instance.date_fin   if self.instance else None)

        if vehicle and date_debut and date_fin:
            if date_fin <= date_debut:
                raise serializers.ValidationError(
                    "La date de fin doit être après la date de début."
                )

            # Chercher conflits : réservations actives qui chevauchent la période
            qs = Reservation.objects.filter(
                vehicle=vehicle,
                statut__in=['en_attente', 'confirmée'],
                date_debut__lt=date_fin,
                date_fin__gt=date_debut,
            )
            # Exclure la réservation courante en cas de mise à jour
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                conflit = qs.first()
                raise serializers.ValidationError(
                    f"Ce véhicule est déjà réservé du {conflit.date_debut} au {conflit.date_fin}. "
                    f"Veuillez choisir une autre période ou un autre véhicule."
                )

        return data


class ReservationDetailSerializer(serializers.ModelSerializer):
    client       = ClientSerializer(read_only=True)
    vehicle_info = serializers.SerializerMethodField()

    class Meta:
        model  = Reservation
        fields = '__all__'

    def get_vehicle_info(self, obj):
        return f"{obj.vehicle.marque} {obj.vehicle.modele} - {obj.vehicle.immatriculation}"


# ✅ NOUVEAU — Serializer Favoris
class FavoriSerializer(serializers.ModelSerializer):
    vehicle_details = VehicleNestedSerializer(source='vehicle', read_only=True)

    class Meta:
        model  = Favori
        fields = ['id', 'vehicle', 'vehicle_details', 'created_at']