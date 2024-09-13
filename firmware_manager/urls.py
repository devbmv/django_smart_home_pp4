from django.urls import path
from firmware_manager import views

urlpatterns = [
    path('update_esp_firmware/', views.update_esp_firmware, name='update_esp_firmware'),
    path('upload_firmware/', views.upload_firmware, name='upload_firmware'),
]
