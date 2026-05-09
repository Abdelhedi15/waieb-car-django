from django.urls import path
from .views import PaiementListView, PaiementDetailView, AvanceListView, AvanceDetailView, ReservationSoldeView

urlpatterns = [
    path('', PaiementListView.as_view()),
    path('<int:pk>/', PaiementDetailView.as_view()),
    path('avances/', AvanceListView.as_view()),
    path('avances/<int:pk>/', AvanceDetailView.as_view()),
    path('solde/<int:reservation_id>/', ReservationSoldeView.as_view()),
]