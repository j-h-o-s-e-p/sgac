import os
from django.core.asgi import get_asgi_application

# Establece el módulo de configuración por defecto
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_asgi_application()
