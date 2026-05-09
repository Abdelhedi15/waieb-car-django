from rest_framework import generics
from .models import Contrat
from .serializers import ContratSerializer

class ContratListView(generics.ListCreateAPIView):
    queryset = Contrat.objects.all()
    serializer_class = ContratSerializer

class ContratDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Contrat.objects.all()
    serializer_class = ContratSerializer