from django.apps import AppConfig

class LightAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "light_app"

    def ready(self):
        from .tasks import start_ping_for_all_users
        
        start_ping_for_all_users()
