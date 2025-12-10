import os
from celery import Celery

# 1. Vincular Celery con la configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('sgac')

# 2. Cargar configuración desde settings.py usando el prefijo 'CELERY_'
app.config_from_object('django.conf:settings', namespace='CELERY')

# 3. Descubrir tareas automáticamente en todas las apps instaladas (tasks.py)
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
