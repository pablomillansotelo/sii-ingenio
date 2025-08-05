from django.apps import AppConfig


class SiiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sii"
    def ready(self):
        import sii.signals  # Asegura que se cargue
