# light_app/middleware.py

from django.utils import translation
from django.conf import settings


class UserSettingsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            user_settings = request.user.usersettings

            # Setăm limba
            translation.activate(user_settings.preferred_language)
            request.LANGUAGE_CODE = user_settings.preferred_language

            # Setăm tema și mărimea fontului în sesiune
            request.session['theme'] = user_settings.theme
            request.session['font_size'] = user_settings.font_size

            # Setăm culoarea principală
            request.session['primary_color'] = user_settings.primary_color
            request.user_ip = user_settings.m5core2_ip if user_settings.m5core2_ip else 'none'
        response = self.get_response(request)

        # Dezactivăm limba după generarea răspunsului
        translation.deactivate()

        return response


class UserLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            user_language = request.user.usersettings.preferred_language
            translation.activate(user_language)
            request.LANGUAGE_CODE = user_language
        else:
            translation.activate('en')  # Limbă implicită dacă utilizatorul nu este autentificat
        response = self.get_response(request)
        translation.deactivate()
        return response
