from django.urls import path
from .views import (
    ClientListView, ClientDetailView,
    ReservationListView, ReservationDetailView,
    ReservationPatchView, CheckPaymentsView, SyncStatutsView,
    PayerResteView, FavorisView,
)

urlpatterns = [
    path('clients/', ClientListView.as_view()),
    path('clients/<int:pk>/', ClientDetailView.as_view()),
    path('reservations/', ReservationListView.as_view()),
    # ✅ Routes fixes AVANT les routes avec <int:pk>
    path('reservations/check-payments/', CheckPaymentsView.as_view()),
    path('reservations/sync-statuts/', SyncStatutsView.as_view()),
    # Routes avec pk
    path('reservations/<int:pk>/', ReservationDetailView.as_view()),
    path('reservations/<int:pk>/state/', ReservationPatchView.as_view()),
    path('reservations/<int:pk>/payer-reste/', PayerResteView.as_view()),
    # ✅ Favoris
    path('favoris/', FavorisView.as_view()),
    path('favoris/<int:vehicle_id>/', FavorisView.as_view()),
]