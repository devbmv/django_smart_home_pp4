from django.contrib import admin
from django.urls import path
from serial_connections import views

urlpatterns = [
    path('serial_data/', views.receive_serial_data, name='receive_serial'),
    path('view_data/', views.view_serial_data, name='uart_page'),
    path('uart_command/', views.uart_command, name='uart_command'),  # URL pentru a procesa comenzile UART

]
