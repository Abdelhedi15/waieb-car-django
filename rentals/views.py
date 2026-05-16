# -*- coding: utf-8 -*-
import threading
from django.conf import settings
from rest_framework import generics
from .models import Client, Reservation
from .serializers import ClientSerializer, ReservationSerializer


def _send_email_mailjet(to_email, to_name, subject, body):
    """Send email via Mailjet API in background thread."""
    def _run():
        try:
            from mailjet_rest import Client as MJClient
            mj = MJClient(auth=(settings.MAILJET_API_KEY, settings.MAILJET_SECRET_KEY), version='v3.1')
            data = {
                'Messages': [{
                    'From': {'Email': settings.MAILJET_FROM_EMAIL, 'Name': settings.MAILJET_FROM_NAME},
                    'To': [{'Email': to_email, 'Name': to_name}],
                    'Subject': subject,
                    'TextPart': body,
                }]
            }
            result = mj.send.create(data=data)
            print(f'[mailjet] Sent to {to_email} status={result.status_code}')
        except Exception as e:
            print(f'[mailjet] Error: {e}')
    threading.Thread(target=_run, daemon=True).start()


def _calculate_acompte(montant_total, date_debut, date_fin):
    if not montant_total or not date_debut or not date_fin:
        return round(float(montant_total) * 20 / 100, 2) if montant_total else 0
    duree = (date_fin - date_debut).days
    if duree <= 3: pct = 20
    elif duree <= 7: pct = 30
    elif duree <= 14: pct = 40
    else: pct = 50
    return round(float(montant_total) * pct / 100, 2)


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
        if hasattr(user, 'role') and user.role == 'client':
            try:
                return Reservation.objects.filter(client=user.client_profile).order_by('-id')
            except Exception:
                return Reservation.objects.none()
        return Reservation.objects.all().order_by('-id')

    def perform_create(self, serializer):
        reservation = serializer.save()
        if reservation.montant_total:
            acompte = _calculate_acompte(reservation.montant_total, reservation.date_debut, reservation.date_fin)
            reservation.acompte = acompte
            reservation.save()
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
        new_statut = reservation.statut
        if old_statut != new_statut and new_statut in ['confirmee', 'annulee', 'confirmée', 'annulée']:
            _send_notification_email(reservation, new_statut)
        return response

    def update(self, request, *args, **kwargs):
        old_statut = self.get_object().statut
        response = super().update(request, *args, **kwargs)
        reservation = self.get_object()
        _sync_vehicle_status(reservation)
        new_statut = reservation.statut
        if old_statut != new_statut and new_statut in ['confirmee', 'annulee', 'confirmée', 'annulée']:
            _send_notification_email(reservation, new_statut)
        return response

    def destroy(self, request, *args, **kwargs):
        reservation = self.get_object()
        response = super().destroy(request, *args, **kwargs)
        try:
            from vehicles.models import Vehicle
            vehicle = Vehicle.objects.get(id=reservation.vehicle_id)
            active = Reservation.objects.filter(vehicle_id=vehicle.id, statut__in=['en_attente','confirmee','confirmée']).exists()
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
        new_statut = reservation.statut
        if old_statut != new_statut and new_statut in ['confirmee', 'annulee', 'confirmée', 'annulée']:
            _send_notification_email(reservation, new_statut)
        return response


def _sync_vehicle_status(reservation):
    try:
        from vehicles.models import Vehicle
        vehicle = Vehicle.objects.get(id=reservation.vehicle_id)
        statut = reservation.statut
        if statut in ['confirmee', 'confirmée']:
            vehicle.statut = 'loue'
        elif statut in ['annulee', 'annulée', 'terminee', 'terminée']:
            other = Reservation.objects.filter(vehicle_id=vehicle.id, statut__in=['confirmee','confirmée']).exclude(id=reservation.id).exists()
            if not other:
                vehicle.statut = 'disponible'
        vehicle.save()
    except Exception as e:
        print(f'[sync] error: {e}')


def _send_notification_email(reservation, statut):
    try:
        client = reservation.client
        email = client.email
        if not email:
            try:
                email = client.user.email
            except Exception:
                pass
        if not email:
            print(f'[email] No email for client {client}')
            return

        vehicle = reservation.vehicle
        nom_client = f'{client.prenom} {client.nom}'
        date_debut = reservation.date_debut
        date_fin = reservation.date_fin
        duree = (date_fin - date_debut).days
        montant_total = reservation.montant_total
        acompte = reservation.acompte
        is_confirmed = statut in ['confirmee', 'confirmée']

        if is_confirmed:
            subject = 'Votre reservation est confirmee - Waieb Car Rent'
            body = (
                f"Bonjour {nom_client},\n\n"
                f"Votre reservation a ete confirmee.\n\n"
                f"Vehicule : {vehicle.marque} {vehicle.modele} ({vehicle.immatriculation})\n"
                f"Debut    : {date_debut}\n"
                f"Fin      : {date_fin}\n"
                f"Duree    : {duree} jour(s)\n"
                f"Total    : {montant_total} DT\n"
                f"Acompte  : {acompte} DT\n\n"
                f"Presentez-vous a notre agence avec votre CIN et permis.\n\n"
                f"Cordialement,\nWaieb Car Rent\nTel: +216 74 000 001"
            )
        else:
            subject = 'Votre reservation a ete annulee - Waieb Car Rent'
            body = (
                f"Bonjour {nom_client},\n\n"
                f"Votre reservation a ete annulee.\n\n"
                f"Vehicule : {vehicle.marque} {vehicle.modele}\n"
                f"Debut    : {date_debut}\n"
                f"Fin      : {date_fin}\n\n"
                f"Pour toute question, contactez-nous.\n\n"
                f"Cordialement,\nWaieb Car Rent"
            )

        _send_email_mailjet(email, nom_client, subject, body)

    except Exception as e:
        print(f'[email] ERROR: {e}')