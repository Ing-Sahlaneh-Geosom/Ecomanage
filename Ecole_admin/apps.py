from django.apps import AppConfig


class EcoleAdminConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Ecole_admin'




class TonAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ton_app"

    def ready(self):
        import Ecole_admin.signals
