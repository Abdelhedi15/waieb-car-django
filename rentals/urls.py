from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ClientListView, ClientDetailView,
    ReservationListView, ReservationDetailView,
    ReservationPatchView, CheckPaymentsView, SyncStatutsView,
    PayerResteView, FavorisView,
    IncidentVehiculeViewSet,
)

router = DefaultRouter()
router.register(r'incidents', IncidentVehiculeViewSet, basename='incident')

urlpatterns = [
    # Clients
    path('clients/', ClientListView.as_view()),
    path('clients/<int:pk>/', ClientDetailView.as_view()),

    # Reservations — routes fixes AVANT <int:pk>
    path('reservations/', ReservationListView.as_view()),
    path('reservations/check-payments/', CheckPaymentsView.as_view()),
    path('reservations/sync-statuts/', SyncStatutsView.as_view()),
    path('reservations/<int:pk>/', ReservationDetailView.as_view()),
    path('reservations/<int:pk>/state/', ReservationPatchView.as_view()),
    path('reservations/<int:pk>/payer-reste/', PayerResteView.as_view()),

    # Favoris
    path('favoris/', FavorisView.as_view()),
    path('favoris/<int:vehicle_id>/', FavorisView.as_view()),

    # Incidents (router) → /incidents/ et /incidents/<id>/
    path('', include(router.urls)),
]