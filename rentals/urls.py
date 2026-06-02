from django.urls import path
from .views import (
    ClientListView, ClientDetailView,
    ReservationListView, ReservationDetailView,
    ReservationPatchView, CheckPaymentsView, SyncStatutsView
)

urlpatterns = [
    path('clients/', ClientListView.as_view()),
    path('clients/<int:pk>/', ClientDetailView.as_view()),
    path('reservations/', ReservationListView.as_view()),
    # ✅ Routes fixes AVANT les routes avec <int:pk>
    path('reservations/check-payments/', CheckPaymentsView.as_view()),
    path('reservations/sync-statuts/', SyncStatutsView.as_view()),
    # Routes avec pk après
    path('reservations/<int:pk>/', ReservationDetailView.as_view()),
    path('reservations/<int:pk>/state/', ReservationPatchView.as_view()),
]