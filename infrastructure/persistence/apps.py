from django.apps import AppConfig


class PersistenceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    # La ruta python real donde está la app
    name = "infrastructure.persistence"
    # El nombre corto que se usa en settings.py y migraciones
    label = "persistence"
