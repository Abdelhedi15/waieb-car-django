from django.urls import path
from .views import VehicleListView, VehicleDetailView, AvailableVehiclesView, send_replacement_email

urlpatterns = [
    path('',           VehicleListView.as_view(),     name='vehicle-list'),
    path('available/', AvailableVehiclesView.as_view(), name='available-vehicles'),
    path('send-replacement-email/', send_replacement_email, name='send-replacement-email'),  # ✅ NEW
    path('<int:pk>/',  VehicleDetailView.as_view(),   name='vehicle-detail'),
]