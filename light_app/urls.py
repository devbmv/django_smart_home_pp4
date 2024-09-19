from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path('settings/', views.user_settings_view, name='user_settings'),
    path("toggle-light/<str:room_name>/<str:light_name>/", views.toggle_light, name="toggle_light"),
    path("rooms/", views.room_list_view, name="room_list"),
    path("lights_status/", views.lights_status, name="lights_status"),  # Adaugă această linie
    path("add_room/", views.add_room, name="add_room"),
    path("edit_room/<int:room_id>/", views.edit_room, name="edit_room"),
    path("delete_room/<int:room_id>/", views.delete_room, name="delete_room"),
    path("add_light/", views.add_light, name="add_light"),
    path("edit_light/<int:light_id>/", views.edit_light, name="edit_light"),
    path("delete_light/<int:light_id>/", views.delete_light, name="delete_light"),
    path('check_server_status/', views.check_server_status, name='check_server_status'),
    path('status_response_for_esp32/', views.status_response_for_esp32, name='status_response_for_esp32'),

]