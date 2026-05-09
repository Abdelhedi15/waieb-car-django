from django.urls import path
from .views import ContratListView, ContratDetailView

urlpatterns = [
    path('', ContratListView.as_view(), name='contrat-list'),
    path('<int:pk>/', ContratDetailView.as_view(), name='contrat-detail'),
]