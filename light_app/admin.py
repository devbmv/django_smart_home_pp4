from django.contrib import admin
from .models import Room, Light, Choice,UserSettings

admin.site.register(Room)
admin.site.register(Light)
admin.site.register(Choice)
admin.site.register(UserSettings)
