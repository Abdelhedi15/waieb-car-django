# -*- coding: utf-8 -*-
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Paiement, Avance
from .serializers import PaiementSerializer, AvanceSerializer
from rentals.models import Reservation


def _auto_confirm_reservation(reservation):
    """
    ✅ Auto-confirme la réservation si un paiement carte est enregistré
    et déclenche email + points fidélité.
    """
    try:
        from rentals.views import _send_notification_email, _award_points, _sync_vehicle_status
        old_statut = reservation.statut

        # Confirmer seulement si encore en attente
        if old_statut in ['en_attente', 'en_attente_rdv']:
            reservation.statut = 'confirmée'
            reservation.save(update_fields=['statut'])

            # Sync statut véhicule
            _sync_vehicle_status(reservation)

            # Email de confirmation au client
            _send_notification_email(reservation, 'confirmée')

            # Points fidélité (+100 pts)
            _award_points(reservation)

            print(f'[auto-confirm] Réservation #{reservation.id} confirmée après paiement carte')
        else:
            print(f'[auto-confirm] Réservation #{reservation.id} déjà en statut "{old_statut}" — pas de changement')

    except Exception as e:
        print(f'[auto-confirm] ERREUR: {e}')


class PaiementListView(generics.ListCreateAPIView):
    queryset = Paiement.objects.all()
    serializer_class = PaiementSerializer

    def perform_create(self, serializer):
        paiement = serializer.save()

        # ✅ FIX PRINCIPAL : auto-confirmer si paiement carte validé
        try:
            reservation = paiement.reservation
            if reservation and paiement.statut == 'payé':
                _auto_confirm_reservation(reservation)
        except Exception as e:
            print(f'[payments] perform_create error: {e}')


class PaiementDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Paiement.objects.all()
    serializer_class = PaiementSerializer

    def perform_update(self, serializer):
        old_statut = serializer.instance.statut
        paiement = serializer.save()

        # ✅ Si un paiement passe à "payé" via PATCH (ex: admin valide manuellement)
        if old_statut != 'payé' and paiement.statut == 'payé':
            try:
                reservation = paiement.reservation
                if reservation:
                    _auto_confirm_reservation(reservation)
            except Exception as e:
                print(f'[payments] perform_update error: {e}')


class AvanceListView(generics.ListCreateAPIView):
    queryset = Avance.objects.all()
    serializer_class = AvanceSerializer


class AvanceDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Avance.objects.all()
    serializer_class = AvanceSerializer


class ReservationSoldeView(APIView):
    def get(self, request, reservation_id):
        try:
            reservation = Reservation.objects.get(id=reservation_id)
            avances = Avance.objects.filter(reservation=reservation)
            paiements = Paiement.objects.filter(reservation=reservation)

            # ✅ Acompte compte comme avance
            acompte = float(reservation.acompte or 0)

            total_avances = sum([
                float(a.montant_especes or 0) + float(a.montant_cheque or 0) +
                float(a.montant_cheque2 or 0) + float(a.montant_virement or 0)
                for a in avances
            ])
            total_paiements = sum([float(p.montant) for p in paiements])
            montant_total = float(reservation.montant_total or 0)

            total_paye = acompte + total_avances + total_paiements
            montant_restant = montant_total - total_paye

            return Response({
                'reservation_id': reservation_id,
                'montant_total': montant_total,
                'acompte': acompte,
                'total_avances': total_avances,
                'total_paiements': total_paiements,
                'total_paye': total_paye,
                'montant_restant': montant_restant,
                'avances': AvanceSerializer(avances, many=True).data,
                'paiements': PaiementSerializer(paiements, many=True).data,
            })
        except Reservation.DoesNotExist:
            return Response({'error': 'Réservation non trouvée'}, status=404)