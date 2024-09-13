from django import forms
from .models import Room, Light, UserSettings
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']

class PasswordUpdateForm(PasswordChangeForm):
    class Meta:
        model = User
        fields = ['password']


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ["name"]
        widgets = {
            'name': forms.TextInput(attrs={'autocomplete': 'name'})
        }

class LightForm(forms.ModelForm):
    class Meta:
        model = Light
        fields = ["name", "room", "description", "state"]
        widgets = {
            'name': forms.TextInput(attrs={'autocomplete': 'off'}),
            'description': forms.Textarea(attrs={'autocomplete': 'off'}),
            'state': forms.Select(attrs={'autocomplete': 'off'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')  # Prinde utilizatorul curent din view
        super(LightForm, self).__init__(*args, **kwargs)
        # Filtrează camerele după utilizatorul curent
        self.fields['room'].queryset = Room.objects.filter(user=user)
        self.fields['room'].widget.attrs.update({'autocomplete': 'off'})

class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        fields = [
            "display_name",
            "email",
            "preferred_language",
            "timezone",
            "theme",
            "font_size",
            "primary_color",
            "email_notifications",
            "push_notifications",
            "two_factor_authentication",
            "scheduled_lights",
            "silence_mode",
            "m5core2_ip",
            'server_check_interval',
        ]
        widgets = {
            'display_name': forms.TextInput(attrs={'autocomplete': 'name'}),
            'email': forms.EmailInput(attrs={'autocomplete': 'email'}),
            'm5core2_ip': forms.TextInput(attrs={'autocomplete': 'off'}),
            'server_check_interval': forms.NumberInput(attrs={'min': 1, 'max': 3600}),
        }
