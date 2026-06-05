from django.urls import path
from .views import LoginView, LogoutView, UserListView, UserDetailView, MeView, ForgotPasswordView

urlpatterns = [
    path('login/', LoginView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('me/', MeView.as_view()),
    path('users/', UserListView.as_view()),
    path('users/<int:pk>/', UserDetailView.as_view()),
    path('forgot-password/', ForgotPasswordView.as_view()),
    
]