from django.urls import path
from .views import (
    ClientListView, ClientDetailView,
    ReservationListView, ReservationDetailView,
    ReservationPatchView
)

urlpatterns = [
    path('clients/', ClientListView.as_view()),
    path('clients/<int:pk>/', ClientDetailView.as_view()),
    path('reservations/', ReservationListView.as_view()),
    path('reservations/<int:pk>/', ReservationDetailView.as_view()),
    path('reservations/<int:pk>/state/', ReservationPatchView.as_view()),
]