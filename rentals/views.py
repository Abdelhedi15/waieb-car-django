# -*- coding: utf-8 -*-
import threading
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from rest_framework import generics, viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .models import Client, Reservation, Favori, IncidentVehicule
from .serializers import (
    ClientSerializer, ReservationSerializer, FavoriSerializer,
    IncidentVehiculeSerializer,
)


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
        today = timezone.now().date()
        statut = reservation.statut

        if statut in ['confirmee', 'confirmée']:
            if reservation.date_debut <= today <= reservation.date_fin:
                vehicle.statut = 'loue'
            else:
                other_active_now = Reservation.objects.filter(
                    vehicle_id=vehicle.id,
                    statut__in=['confirmee', 'confirmée'],
                    date_debut__lte=today,
                    date_fin__gte=today,
                ).exclude(id=reservation.id).exists()
                vehicle.statut = 'loue' if other_active_now else 'disponible'

        elif statut in ['annulee', 'annulée', 'terminee', 'terminée']:
            other_active_now = Reservation.objects.filter(
                vehicle_id=vehicle.id,
                statut__in=['confirmee', 'confirmée'],
                date_debut__lte=today,
                date_fin__gte=today,
            ).exclude(id=reservation.id).exists()
            if not other_active_now:
                vehicle.statut = 'disponible'

        vehicle.save()
    except Exception as e:
        print(f'[sync] error: {e}')


def _get_montant_restant(reservation):
    try:
        from payments.models import Paiement, Avance
        total_paiements = sum(float(p.montant) for p in Paiement.objects.filter(reservation=reservation))
        total_avances   = sum(float(a.montant_total) for a in Avance.objects.filter(reservation=reservation))
        acompte = float(reservation.acompte or 0)
        total_paye = total_paiements + total_avances + acompte
        return max(0, float(reservation.montant_total or 0) - total_paye)
    except Exception as e:
        print(f'[montant_restant] error: {e}')
        return max(0, float(reservation.montant_total or 0) - float(reservation.acompte or 0))


def _send_notification_email(reservation, statut):
    try:
        client = reservation.client
        email = client.email
        if not email:
            try: email = client.user.email
            except Exception: pass
        if not email:
            return
        vehicle = reservation.vehicle
        nom_client = f'{client.prenom} {client.nom}'
        date_debut = reservation.date_debut
        date_fin   = reservation.date_fin
        duree      = (date_fin - date_debut).days
        montant_total = reservation.montant_total
        acompte    = reservation.acompte
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


# ══════════════════════════════════════════════════════════════
# VIEWS
# ══════════════════════════════════════════════════════════════

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
        data       = serializer.validated_data
        vehicle    = data.get('vehicle')
        client     = data.get('client')
        date_debut = data.get('date_debut')
        date_fin   = data.get('date_fin')

        if date_debut and date_fin:
            # ── Blocage 1 : même véhicule sur la même période ─────────────
            if vehicle:
                vehicle_conflict = Reservation.objects.filter(
                    vehicle_id=vehicle.id,
                    statut__in=['confirmée', 'confirmee', 'en_attente'],
                    date_debut__lte=date_fin,
                    date_fin__gte=date_debut,
                ).exists()
                if vehicle_conflict:
                    raise ValidationError({
                        'error': 'Ce véhicule est déjà réservé sur cette période. Veuillez choisir un autre véhicule ou modifier les dates.',
                        'code': 'doublon_vehicule',
                    })

            # ── Blocage 2 : même client sur la même période ───────────────
            if client:
                client_id = client.id if hasattr(client, 'id') else client
                client_conflict = Reservation.objects.filter(
                    client_id=client_id,
                    statut__in=['confirmée', 'confirmee', 'en_attente'],
                    date_debut__lte=date_fin,
                    date_fin__gte=date_debut,
                ).exists()
                if client_conflict:
                    raise ValidationError({
                        'error': 'Ce client a déjà une réservation active sur cette période. Un client ne peut pas avoir deux locations simultanées.',
                        'code': 'doublon_client',
                    })

        reservation = serializer.save()
        if reservation.montant_total:
            acompte = _calculate_acompte(
                reservation.montant_total,
                reservation.date_debut,
                reservation.date_fin,
            )
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
            active_now = Reservation.objects.filter(
                vehicle_id=vehicle.id,
                statut__in=['en_attente', 'confirmee', 'confirmée'],
                date_debut__lte=today,
                date_fin__gte=today,
            ).exists()
            if not active_now:
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


class CheckPaymentsView(APIView):
    permission_classes = []

    def get(self, request):
        today = timezone.now().date()
        tomorrow = today + timedelta(days=1)
        results = {'emails_j1': [], 'annulations': [], 'errors': []}

        for r in Reservation.objects.filter(
            statut__in=['confirmée', 'confirmee', 'en_attente'],
            date_fin=tomorrow,
        ):
            try:
                montant_restant = _get_montant_restant(r)
                if montant_restant > 0:
                    client = r.client
                    email = client.email or (client.user.email if client.user else None)
                    if email:
                        _send_email_mailjet(
                            email, f'{client.prenom} {client.nom}',
                            '⚠️ Rappel paiement — Waieb Car Rent',
                            f"Bonjour {client.prenom} {client.nom},\n\n"
                            f"Votre location se termine DEMAIN ({r.date_fin}).\n"
                            f"Vehicule : {r.vehicle.marque} {r.vehicle.modele}\n"
                            f"Montant restant : {montant_restant:.2f} DT\n\n"
                            f"Merci de regler ce montant lors de la restitution.\n\n"
                            f"Cordialement,\nWaieb Car Rent"
                        )
                        results['emails_j1'].append({'reservation': r.id, 'montant_restant': montant_restant})
            except Exception as e:
                results['errors'].append(f'Email J-1 #{r.id}: {str(e)}')

        for r in Reservation.objects.filter(
            statut__in=['confirmée', 'confirmee', 'en_attente'],
            date_fin__lt=today,
        ):
            try:
                montant_restant = _get_montant_restant(r)
                if montant_restant > 0:
                    r.statut = 'annulée'
                    r.notes = (r.notes or '') + f' | AUTO-ANNULE {today}: {montant_restant:.2f} DT non paye'
                    r.save()
                    try:
                        vehicle = r.vehicle
                        still_active = Reservation.objects.filter(
                            vehicle_id=vehicle.id,
                            statut__in=['en_attente', 'confirmee', 'confirmée'],
                            date_debut__lte=today,
                            date_fin__gte=today,
                        ).exclude(id=r.id).exists()
                        if not still_active:
                            vehicle.statut = 'disponible'
                            vehicle.save()
                    except Exception as ve:
                        results['errors'].append(f'Vehicule #{r.id}: {str(ve)}')
                    results['annulations'].append({'reservation': r.id, 'montant_restant': montant_restant})
            except Exception as e:
                results['errors'].append(f'Annulation #{r.id}: {str(e)}')

        return Response({'status': 'done', 'date': str(today),
                         'emails_j1': len(results['emails_j1']),
                         'annulations': len(results['annulations']),
                         'details': results})


class SyncStatutsView(APIView):
    permission_classes = []

    def get(self, request):
        from vehicles.models import Vehicle
        today = timezone.now().date()
        updated = []
        for vehicle in Vehicle.objects.filter(statut='loue'):
            active_now = Reservation.objects.filter(
                vehicle_id=vehicle.id,
                statut__in=['confirmee', 'confirmée', 'en_attente'],
                date_debut__lte=today,
                date_fin__gte=today,
            ).exists()
            if not active_now:
                vehicle.statut = 'disponible'
                vehicle.save()
                updated.append(f'{vehicle.marque} {vehicle.modele} ({vehicle.immatriculation})')
        return Response({'status': 'done', 'vehicules_liberes': len(updated), 'details': updated})


class PayerResteView(APIView):
    def post(self, request, pk):
        try:
            reservation = Reservation.objects.get(pk=pk)
            client = reservation.client
            email = client.email or (client.user.email if hasattr(client, 'user') and client.user else None)

            if hasattr(reservation, 'acompte_paye'):
                reservation.acompte_paye = True
                reservation.save(update_fields=['acompte_paye'])

            acompte = float(reservation.acompte or 0)
            total   = float(reservation.montant_total or 0)
            restant = max(0, total - acompte)
            mode     = request.data.get('mode', 'carte')
            rdv_date = request.data.get('rdv_date', '')
            rdv_heure= request.data.get('rdv_heure', '')

            if email:
                vehicle = reservation.vehicle
                nom_client = f'{client.prenom} {client.nom}'
                if mode == 'carte':
                    subject = '✅ Paiement reçu — Waieb Car Rent'
                    body = (
                        f"Bonjour {nom_client},\n\n"
                        f"Nous avons bien reçu votre paiement du solde restant.\n\n"
                        f"Réservation  : #{reservation.id}\n"
                        f"Véhicule     : {vehicle.marque} {vehicle.modele} ({vehicle.immatriculation})\n"
                        f"Période      : {reservation.date_debut} → {reservation.date_fin}\n"
                        f"Montant payé : {restant:.2f} DT\n\n"
                        f"Votre réservation est entièrement soldée. À bientôt !\n\n"
                        f"Cordialement,\nWaieb Car Rent"
                    )
                else:
                    subject = '📅 RDV enregistré — Paiement Waieb Car Rent'
                    body = (
                        f"Bonjour {nom_client},\n\n"
                        f"Votre rendez-vous pour le paiement en espèces a bien été enregistré.\n\n"
                        f"Réservation  : #{reservation.id}\n"
                        f"Véhicule     : {vehicle.marque} {vehicle.modele} ({vehicle.immatriculation})\n"
                        f"Période      : {reservation.date_debut} → {reservation.date_fin}\n"
                        f"Montant dû   : {restant:.2f} DT\n"
                        f"RDV          : {rdv_date} à {rdv_heure}\n\n"
                        f"Présentez-vous à notre agence à l'heure du RDV avec votre CIN.\n\n"
                        f"Cordialement,\nWaieb Car Rent"
                    )
                _send_email_mailjet(email, nom_client, subject, body)

            return Response({'status': 'ok', 'email_sent': bool(email)})
        except Reservation.DoesNotExist:
            return Response({'error': 'Réservation introuvable'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=500)


class FavorisView(APIView):
    def _get_client(self, request):
        try: return request.user.client_profile
        except Exception: return None

    def get(self, request):
        client = self._get_client(request)
        if not client:
            return Response([], status=200)
        favoris = Favori.objects.filter(client=client).select_related('vehicle')
        return Response(FavoriSerializer(favoris, many=True, context={'request': request}).data)

    def post(self, request):
        client = self._get_client(request)
        if not client:
            return Response({'error': 'Non authentifié'}, status=401)
        vehicle_id = request.data.get('vehicle_id')
        if not vehicle_id:
            return Response({'error': 'vehicle_id requis'}, status=400)
        try:
            from vehicles.models import Vehicle
            vehicle = Vehicle.objects.get(pk=vehicle_id)
            favori, created = Favori.objects.get_or_create(client=client, vehicle=vehicle)
            return Response({'status': 'added' if created else 'already_exists', 'id': favori.id})
        except Vehicle.DoesNotExist:
            return Response({'error': 'Véhicule introuvable'}, status=404)

    def delete(self, request, vehicle_id=None):
        client = self._get_client(request)
        if not client:
            return Response({'error': 'Non authentifié'}, status=401)
        if not vehicle_id:
            return Response({'error': 'vehicle_id requis'}, status=400)
        deleted, _ = Favori.objects.filter(client=client, vehicle_id=vehicle_id).delete()
        return Response({'status': 'removed' if deleted else 'not_found'})


# ══════════════════════════════════════════════════════════════
# IncidentVehiculeViewSet
# ══════════════════════════════════════════════════════════════
class IncidentVehiculeViewSet(viewsets.ModelViewSet):
    queryset = IncidentVehicule.objects.select_related('vehicle', 'reservation').all()
    serializer_class = IncidentVehiculeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        vehicle_id     = self.request.query_params.get('vehicle')
        reservation_id = self.request.query_params.get('reservation')
        type_incident  = self.request.query_params.get('type_incident')
        repare         = self.request.query_params.get('repare')

        if vehicle_id:     qs = qs.filter(vehicle_id=vehicle_id)
        if reservation_id: qs = qs.filter(reservation_id=reservation_id)
        if type_incident:  qs = qs.filter(type_incident=type_incident)
        if repare is not None:
            qs = qs.filter(repare=(repare.lower() == 'true'))
        return qs