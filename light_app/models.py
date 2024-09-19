from django.db import models
from django.contrib.auth.models import User
import datetime

# =============================================================================

STATE_CHOICES = [
    (1, "on"),
    (2, "off"),
    (3, "timer"),
]

# =============================================================================


class Choice(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


# =============================================================================


class Room(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="rooms",default=1
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


# =============================================================================


class Light(models.Model):
    name = models.CharField(max_length=100, default="")
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="lights")
    description = models.TextField(null=True,blank=True, default="")
    state = models.IntegerField(choices=STATE_CHOICES, default=2)
    choices = models.ManyToManyField(Choice, related_name="lights", blank=True)

    def __str__(self):
        return f"{self.name} in {self.room}"

    class Meta:
        ordering = ["id"]


# =============================================================================


class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    api_password = models.CharField(max_length=128)  # Parola pentru API

    server_check_interval = models.IntegerField(
        default=5, help_text="Interval in seconds for checking server status."
    )

    display_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(max_length=255, blank=True)
    preferred_language = models.CharField(
        max_length=50,
        choices=[("en", "English"), ("fr", "French"), ("de", "German")],
        default="en",
    )
    timezone = models.CharField(max_length=50, default="UTC")
    theme = models.CharField(
        max_length=10, choices=[("light", "Light"), ("dark", "Dark")], default="light"
    )
    font_size = models.CharField(
        max_length=10,
        choices=[("small", "Small"), ("medium", "Medium"), ("large", "Large")],
        default="medium",
    )
    primary_color = models.CharField(max_length=7, default="#2980b9")  # Hex color
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    two_factor_authentication = models.BooleanField(default=False)
    scheduled_lights = models.BooleanField(default=False)
    silence_mode = models.BooleanField(default=False)
    m5core2_ip = models.CharField(
        max_length=100, blank=True, default=""
    )  # Adresa IP a utilizatorului pentru M5Core2

    def save(self, *args, **kwargs):
        # Ensure the value is between 5 seconds (min) and 7200 seconds (2 hour)
        if self.server_check_interval < 1:
            self.server_check_interval = 1
        elif self.server_check_interval > 7200:
            self.server_check_interval = 7200
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} Settings"