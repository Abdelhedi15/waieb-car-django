from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Paiement, Avance
from .serializers import PaiementSerializer, AvanceSerializer
from rentals.models import Reservation

class PaiementListView(generics.ListCreateAPIView):
    queryset = Paiement.objects.all()
    serializer_class = PaiementSerializer

class PaiementDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Paiement.objects.all()
    serializer_class = PaiementSerializer

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

            # ✅ Total payé = acompte + avances + paiements
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