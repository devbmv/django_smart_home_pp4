# home_control_project/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("accounts/", include("allauth.urls")),
    path("admin/", admin.site.urls),
    path('esp/', include('serial_connections.urls')),  # Rute pentru ESP32 și date seriale
    path('update/', include('firmware_manager.urls')),  # Rute pentru ESP32 și date seriale
    path("", include("light_app.urls")),
    path("summernote/", include("django_summernote.urls")),
]
