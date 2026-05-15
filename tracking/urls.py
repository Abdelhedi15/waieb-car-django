from django.urls import path
from .views import (
    UpdateLocationView, AllLocationsView, StopSharingView,
    ChatView, EmployeeChatView, ClientChatHistoryView,
)

urlpatterns = [
    # GPS
    path('location/update/', UpdateLocationView.as_view()),
    path('location/all/', AllLocationsView.as_view()),
    path('location/stop/', StopSharingView.as_view()),
    # Chat
    path('chat/', ChatView.as_view()),
    path('chat/employee/', EmployeeChatView.as_view()),
    path('chat/employee/<int:client_id>/', ClientChatHistoryView.as_view()),
]