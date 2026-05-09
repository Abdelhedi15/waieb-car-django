from rest_framework import generics
from rest_framework.response import Response
from .models import Client, Reservation
from .serializers import ClientSerializer, ReservationSerializer
from django.core.mail import send_mail
from django.conf import settings


class ClientListView(generics.ListCreateAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer


class ClientDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer


class ReservationListView(generics.ListCreateAPIView):
    serializer_class = ReservationSerializer

    def get_queryset(self):
        user = self.request.user
        # ── Client sees ONLY his own reservations
        if hasattr(user, 'role') and user.role == 'client':
            try:
                client = user.client_profile
                return Reservation.objects.filter(
                    client=client).order_by('-id')
            except Exception:
                return Reservation.objects.none()
        # ── Admin/Employee sees ALL reservations
        return Reservation.objects.all().order_by('-id')

    def perform_create(self, serializer):
        reservation = serializer.save()
        _sync_vehicle_status(reservation)


class ReservationDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    http_method_names = ['get', 'put', 'patch', 'delete', 'head', 'options']

    def partial_update(self, request, *args, **kwargs):
        old_statut = self.get_object().statut
        kwargs['partial'] = True
        response = self.update(request, *args, **kwargs)
        reservation = self.get_object()
        _sync_vehicle_status(reservation)
        if old_statut != reservation.statut and reservation.statut in ['confirmée', 'annulée']:
            _send_notification_email(reservation, reservation.statut)
        return response

    def update(self, request, *args, **kwargs):
        old_statut = self.get_object().statut
        response = super().update(request, *args, **kwargs)
        reservation = self.get_object()
        _sync_vehicle_status(reservation)
        if old_statut != reservation.statut and reservation.statut in ['confirmée', 'annulée']:
            _send_notification_email(reservation, reservation.statut)
        return response

    def destroy(self, request, *args, **kwargs):
        reservation = self.get_object()
        response = super().destroy(request, *args, **kwargs)
        try:
            from vehicles.models import Vehicle
            vehicle = Vehicle.objects.get(id=reservation.vehicle_id)
            active = Reservation.objects.filter(
                vehicle_id=vehicle.id,
                statut__in=['en_attente', 'confirmée']
            ).exists()
            if not active:
                vehicle.statut = 'disponible'
                vehicle.save()
        except Exception:
            pass
        return response


class ReservationPatchView(generics.UpdateAPIView):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    http_method_names = ['patch', 'put']

    def partial_update(self, request, *args, **kwargs):
        old_statut = self.get_object().statut
        kwargs['partial'] = True
        response = self.update(request, *args, **kwargs)
        reservation = self.get_object()
        _sync_vehicle_status(reservation)
        if old_statut != reservation.statut and reservation.statut in ['confirmée', 'annulée']:
            _send_notification_email(reservation, reservation.statut)
        return response


def _sync_vehicle_status(reservation):
    try:
        from vehicles.models import Vehicle
        vehicle = Vehicle.objects.get(id=reservation.vehicle_id)
        if reservation.statut == 'confirmée':
            vehicle.statut = 'loué'
        elif reservation.statut in ['annulée', 'terminée']:
            other_active = Reservation.objects.filter(
                vehicle_id=vehicle.id,
                statut='confirmée'
            ).exclude(id=reservation.id).exists()
            if not other_active:
                vehicle.statut = 'disponible'
        vehicle.save()
    except Exception as e:
        print(f'[sync_vehicle_status] error: {e}')


def _send_notification_email(reservation, statut):
    try:
        client = reservation.client
        email  = client.email
        if not email:
            try:
                if client.user and client.user.email:
                    email = client.user.email
            except Exception:
                pass
        if not email:
            print(f'[email] No email found for client {client}')
            return

        vehicle    = reservation.vehicle
        nom_client = f'{client.prenom} {client.nom}'

        if statut == 'confirmée':
            subject = '✅ Votre réservation est confirmée — Waieb Car'
            message = f"""Bonjour {nom_client},

Excellente nouvelle ! Votre réservation a été confirmée.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚗  Véhicule   : {vehicle.marque} {vehicle.modele} ({vehicle.immatriculation})
📅  Début      : {reservation.date_debut}
📅  Fin        : {reservation.date_fin}
💰  Total      : {reservation.montant_total} DT
💳  Acompte    : {reservation.acompte} DT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Présentez-vous à notre agence à la date de début de votre location.
N'oubliez pas votre CIN et permis de conduire.

Cordialement,
Waieb Car Rent 🚗
"""
        else:
            subject = '❌ Votre réservation a été annulée — Waieb Car'
            message = f"""Bonjour {nom_client},

Nous vous informons que votre réservation #{reservation.id} a été annulée.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚗  Véhicule   : {vehicle.marque} {vehicle.modele}
📅  Début      : {reservation.date_debut}
📅  Fin        : {reservation.date_fin}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Pour toute question, contactez-nous.

Cordialement,
Waieb Car Rent 🚗
"""
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=True,
        )
        print(f'[email] ✅ Sent to {email} — statut: {statut}')

    except Exception as e:
        print(f'[email] ❌ Error: {e}')