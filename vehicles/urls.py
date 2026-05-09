from django.urls import path
from .views import VehicleListView, VehicleDetailView, AvailableVehiclesView

urlpatterns = [
    path('', VehicleListView.as_view(), name='vehicle-list'),
    path('available/', AvailableVehiclesView.as_view(), name='available-vehicles'),  # ← BEFORE <int:pk>
    path('<int:pk>/', VehicleDetailView.as_view(), name='vehicle-detail'),
]