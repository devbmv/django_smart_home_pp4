from django.utils import translation
from django.conf import settings
from light_app.models import UserSettings 

class UserSettingsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            user_settings, created = UserSettings.objects.get_or_create(user=request.user)

            translation.activate(user_settings.preferred_language)
            request.LANGUAGE_CODE = user_settings.preferred_language

            request.session['theme'] = user_settings.theme
            request.session['font_size'] = user_settings.font_size

            request.session['primary_color'] = user_settings.primary_color
            request.user_ip = user_settings.m5core2_ip if user_settings.m5core2_ip else 'none'
        response = self.get_response(request)

        translation.deactivate()

        return response


class UserLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            user_settings, created = UserSettings.objects.get_or_create(user=request.user)
            translation.activate(user_settings.preferred_language)
            request.LANGUAGE_CODE = user_settings.preferred_language
        else:
            translation.activate('en')  
        response = self.get_response(request)
        translation.deactivate()
        return response
