import os
from pathlib import Path
from decouple import config
from django.contrib.messages import constants as messages

# ==================== RUTAS BASE ====================
BASE_DIR = Path(__file__).resolve().parent.parent

# ==================== SEGURIDAD ====================
SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,web').split(',')

# Orígenes confiables para protección CSRF (Importante para despliegue)
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000", "http://127.0.0.1:8000",
    "https://localhost:8000", "https://127.0.0.1:8000",
    "https://*.github.dev",
    "https://*.app.github.dev",
    "https://*.app.github.dev/admin/logout/",
    "https://*.app.github.dev/admin",
]

X_FRAME_OPTIONS = 'SAMEORIGIN'

# ==================== APLICACIONES ====================
INSTALLED_APPS = [
    # Apps nativas
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Librerías de terceros
    'rest_framework',
    'rest_framework.authtoken',
    'drf_spectacular', # Documentación API
    'corsheaders',     # Manejo de CORS
    
    # --- Arquitectura Limpia (Apps Locales) ---
    # Infraestructura: Persistencia y modelos de datos
    'infrastructure.persistence.apps.PersistenceConfig', 
    # Presentación: Web, Vistas, Templates
    'presentation',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Servir estáticos optimizados
    'corsheaders.middleware.CorsMiddleware',      # Headers CORS antes de respuestas comunes
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'presentation' / 'templates'], # Ruta explícita a templates
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ==================== BASE DE DATOS ====================
# Configuración vía variables de entorno (DB_*)
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.postgresql'),
        'NAME': config('DB_NAME', default='sgac_db'),
        'USER': config('DB_USER', default='sgac_user'),
        'PASSWORD': config('DB_PASSWORD', default='sgac_password'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

# Modelo de Usuario Personalizado (Esencial definirlo al inicio del proyecto)
AUTH_USER_MODEL = 'persistence.CustomUser'

# ==================== CACHE & CELERY (REDIS) ====================
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')

# Configuración Celery
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

# Configuración Caché (Usando Redis)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# ==================== VALIDACIÓN DE PASSWORD ====================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ==================== LOCALIZACIÓN ====================
LANGUAGE_CODE = 'es-pe'
TIME_ZONE = 'America/Lima'
USE_I18N = True
USE_TZ = True

# ==================== ESTÁTICOS Y MEDIA ====================
# URLs
STATIC_URL = '/static/'
MEDIA_URL = '/media/'

# Rutas físicas
STATIC_ROOT = BASE_DIR / 'staticfiles' # Donde WhiteNoise recolecta los estáticos
MEDIA_ROOT = BASE_DIR / 'media'        # Archivos subidos por usuario

# Carpetas adicionales de estáticos (desarrollo)
STATICFILES_DIRS = [
    BASE_DIR / 'presentation' / 'static',
]

# Motores de almacenamiento (Whitenoise para producción)
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==================== DRF & API ====================
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'SGAC API',
    'DESCRIPTION': 'Sistema de Gestión Académica Complementario',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# Configuración CORS (Permitir frontend React/Vue/etc)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CORS_ALLOW_CREDENTIALS = True

# ==================== LOGGING ====================
# Crea carpeta logs si no existe
LOG_DIR = BASE_DIR / 'logs'
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'sgac.log',
            'maxBytes': 1024 * 1024 * 5,  # 5 MB por archivo
            'backupCount': 5,              # Mantener 5 archivos de backup
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}

# ==================== UI HELPERS ====================
# Mapeo de etiquetas de mensajes de Django a clases de Bootstrap 5
MESSAGE_TAGS = {
    messages.DEBUG: 'secondary',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning', 
    messages.ERROR: 'danger',   
}