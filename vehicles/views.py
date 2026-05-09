from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny        # ← add this import
from .models import Vehicle
from .serializers import VehicleSerializer

class VehicleListView(generics.ListCreateAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    parser_classes = [MultiPartParser, FormParser]

class VehicleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    parser_classes = [MultiPartParser, FormParser]

class AvailableVehiclesView(APIView):
    permission_classes = [AllowAny]                    # ← add this line

    def get(self, request):
        date_debut = request.query_params.get('date_debut')
        date_fin = request.query_params.get('date_fin')
        if not date_debut or not date_fin:
            return Response({'error': 'date_debut and date_fin required'}, status=400)
        from rentals.models import Reservation
        reserved_ids = Reservation.objects.filter(
            statut__in=['en_attente', 'confirmée'],
            date_debut__lte=date_fin,
            date_fin__gte=date_debut
        ).values_list('vehicle_id', flat=True)
        available = Vehicle.objects.exclude(id__in=reserved_ids).filter(statut='disponible')
        return Response(VehicleSerializer(available, many=True).data)