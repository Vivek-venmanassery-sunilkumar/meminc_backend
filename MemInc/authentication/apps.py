from django.apps import AppConfig
import sys

class AuthenticationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authentication'

    def ready(self):
        if 'test' not in sys.argv:
            import authentication.signals

