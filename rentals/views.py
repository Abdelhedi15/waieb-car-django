# -*- coding: utf-8 -*-
import threading
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Client, Reservation
from .serializers import ClientSerializer, ReservationSerializer


def _send_email_mailjet(to_email, to_name, subject, body):
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


def _award_points(reservation):
    try:
        client = reservation.client
        client.points_gagnes = (client.points_gagnes or 0) + 100
        client.save(update_fields=['points_gagnes'])
        print(f'[points] +100 pts -> client {client.id} | total: {client.points_gagnes}')
    except Exception as e:
        print(f'[points] error: {e}')


def _sync_vehicle_status(reservation):
    try:
        from vehicles.models import Vehicle
        vehicle = Vehicle.objects.get(id=reservation.vehicle_id)
        statut = reservation.statut
        today = timezone.now().date()

        if statut in ['confirmee', 'confirmée']:
            # ✅ Si date_fin passée → libérer automatiquement
            if reservation.date_fin < today:
                vehicle.statut = 'disponible'
            else:
                vehicle.statut = 'loue'
        elif statut in ['annulee', 'annulée', 'terminee', 'terminée']:
            # Vérifier s'il y a d'autres réservations actives FUTURES
            other = Reservation.objects.filter(
                vehicle_id=vehicle.id,
                statut__in=['confirmee', 'confirmée'],
                date_fin__gte=today,
            ).exclude(id=reservation.id).exists()
            if not other:
                vehicle.statut = 'disponible'
        vehicle.save()
    except Exception as e:
        print(f'[sync] error: {e}')


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
        new_statut = reservation.statut
        _sync_vehicle_status(reservation)
        if old_statut != new_statut and new_statut in ['confirmee', 'annulee', 'confirmée', 'annulée']:
            _send_notification_email(reservation, new_statut)
        if old_statut != new_statut and new_statut in ['confirmee', 'confirmée', 'terminee', 'terminée']:
            _award_points(reservation)
        return response

    def update(self, request, *args, **kwargs):
        old_statut = self.get_object().statut
        response = super().update(request, *args, **kwargs)
        reservation = self.get_object()
        new_statut = reservation.statut
        _sync_vehicle_status(reservation)
        if old_statut != new_statut and new_statut in ['confirmee', 'annulee', 'confirmée', 'annulée']:
            _send_notification_email(reservation, new_statut)
        if old_statut != new_statut and new_statut in ['confirmee', 'confirmée', 'terminee', 'terminée']:
            _award_points(reservation)
        return response

    def destroy(self, request, *args, **kwargs):
        reservation = self.get_object()
        response = super().destroy(request, *args, **kwargs)
        try:
            from vehicles.models import Vehicle
            vehicle = Vehicle.objects.get(id=reservation.vehicle_id)
            today = timezone.now().date()
            active = Reservation.objects.filter(
                vehicle_id=vehicle.id,
                statut__in=['en_attente', 'confirmee', 'confirmée'],
                date_fin__gte=today,
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
        new_statut = reservation.statut
        _sync_vehicle_status(reservation)
        if old_statut != new_statut and new_statut in ['confirmee', 'annulee', 'confirmée', 'annulée']:
            _send_notification_email(reservation, new_statut)
        if old_statut != new_statut and new_statut in ['confirmee', 'confirmée', 'terminee', 'terminée']:
            _award_points(reservation)
        return response


# ✅ NOUVEAU: Vérification paiements + alertes + auto-annulation
class CheckPaymentsView(APIView):
    """
    GET /api/reservations/check-payments/
    - Email J-1 aux clients avec montant restant
    - Auto-annulation + libération véhicule si non payé après date_fin
    """
    permission_classes = []

    def get(self, request):
        today = timezone.now().date()
        tomorrow = today + timedelta(days=1)

        results = {'emails_j1': [], 'annulations': [], 'errors': []}

        # ── Email J-1
        for r in Reservation.objects.filter(
            statut__in=['confirmée', 'confirmee', 'en_attente'],
            date_fin=tomorrow,
        ):
            try:
                from payments.models import Payment
                total_paye = sum(float(p.montant) for p in Payment.objects.filter(reservation=r))
                montant_restant = float(r.montant_total or 0) - total_paye
                if montant_restant > 0:
                    client = r.client
                    email = client.email or (client.user.email if client.user else None)
                    if email:
                        _send_email_mailjet(
                            email, f'{client.prenom} {client.nom}',
                            '⚠️ Rappel paiement — Waieb Car Rent',
                            f"Bonjour {client.prenom} {client.nom},\n\n"
                            f"Votre location se termine DEMAIN ({r.date_fin}).\n"
                            f"Véhicule : {r.vehicle.marque} {r.vehicle.modele}\n"
                            f"Montant restant : {montant_restant:.2f} DT\n\n"
                            f"Merci de régler ce montant lors de la restitution.\n\n"
                            f"Cordialement,\nWaieb Car Rent"
                        )
                        results['emails_j1'].append({
                            'reservation': r.id,
                            'client': f'{client.prenom} {client.nom}',
                            'montant_restant': montant_restant,
                        })
            except Exception as e:
                results['errors'].append(f'Email J-1 #{r.id}: {str(e)}')

        # ── Auto-annulation : date_fin passée + montant restant
        for r in Reservation.objects.filter(
            statut__in=['confirmée', 'confirmee', 'en_attente'],
            date_fin__lt=today,
        ):
            try:
                from payments.models import Payment
                total_paye = sum(float(p.montant) for p in Payment.objects.filter(reservation=r))
                montant_restant = float(r.montant_total or 0) - total_paye
                if montant_restant > 0:
                    r.statut = 'annulée'
                    r.notes = (r.notes or '') + f' | AUTO-ANNULÉ {today}: {montant_restant:.2f} DT non payé'
                    r.save()
                    # Libérer le véhicule
                    try:
                        vehicle = r.vehicle
                        still_active = Reservation.objects.filter(
                            vehicle_id=vehicle.id,
                            statut__in=['en_attente', 'confirmee', 'confirmée'],
                            date_fin__gte=today,
                        ).exclude(id=r.id).exists()
                        if not still_active:
                            vehicle.statut = 'disponible'
                            vehicle.save()
                    except Exception as ve:
                        results['errors'].append(f'Véhicule #{r.id}: {str(ve)}')
                    results['annulations'].append({
                        'reservation': r.id,
                        'client': f'{r.client.prenom} {r.client.nom}',
                        'montant_restant': montant_restant,
                    })
            except Exception as e:
                results['errors'].append(f'Annulation #{r.id}: {str(e)}')

        return Response({
            'status': 'done',
            'date': str(today),
            'emails_j1': len(results['emails_j1']),
            'annulations': len(results['annulations']),
            'details': results,
        })


# ✅ NOUVEAU: Sync statuts véhicules
class SyncStatutsView(APIView):
    """
    GET /api/reservations/sync-statuts/
    Libère les véhicules dont toutes les réservations sont terminées
    """
    permission_classes = []

    def get(self, request):
        from vehicles.models import Vehicle
        today = timezone.now().date()
        updated = []

        for vehicle in Vehicle.objects.filter(statut='loue'):
            active = Reservation.objects.filter(
                vehicle_id=vehicle.id,
                statut__in=['confirmee', 'confirmée', 'en_attente'],
                date_fin__gte=today,
            ).exists()
            if not active:
                vehicle.statut = 'disponible'
                vehicle.save()
                updated.append(f'{vehicle.marque} {vehicle.modele} ({vehicle.immatriculation})')

        return Response({
            'status': 'done',
            'vehicules_liberes': len(updated),
            'details': updated,
        })


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
                f"Bonjour {nom_client},\n\nVotre reservation a ete confirmee.\n\n"
                f"Vehicule : {vehicle.marque} {vehicle.modele} ({vehicle.immatriculation})\n"
                f"Debut    : {date_debut}\nFin      : {date_fin}\n"
                f"Duree    : {duree} jour(s)\nTotal    : {montant_total} DT\n"
                f"Acompte  : {acompte} DT\n\n"
                f"Presentez-vous a notre agence avec votre CIN et permis.\n\n"
                f"Cordialement,\nWaieb Car Rent"
            )
        else:
            subject = 'Votre reservation a ete annulee - Waieb Car Rent'
            body = (
                f"Bonjour {nom_client},\n\nVotre reservation a ete annulee.\n\n"
                f"Vehicule : {vehicle.marque} {vehicle.modele}\n"
                f"Debut    : {date_debut}\nFin      : {date_fin}\n\n"
                f"Cordialement,\nWaieb Car Rent"
            )
        _send_email_mailjet(email, nom_client, subject, body)
    except Exception as e:
        print(f'[email] ERROR: {e}')