from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/vehicles/', include('vehicles.urls')),
    path('api/', include('rentals.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/contracts/', include('contracts.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)