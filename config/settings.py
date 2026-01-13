import os
import sys
from pathlib import Path
from decouple import config
from django.contrib.messages import constants as messages

# ==================== RUTAS BASE ====================
BASE_DIR = Path(__file__).resolve().parent.parent

# ==================== SECRETOS & DEBUG ====================
SECRET_KEY = config("SECRET_KEY", default="django-insecure-dev-key")
DEBUG = config("DEBUG", default=True, cast=bool)

# ==================== CONFIGURACIÓN DE RED Y CODESPACES ====================
# Hosts permitidos base
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1,web").split(",")

# Variables de entorno de Codespaces
CODESPACE_NAME = os.getenv("CODESPACE_NAME")
CODESPACE_DOMAIN = os.getenv("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN")

# 1. Agregar Host dinámico de Codespaces a ALLOWED_HOSTS
if CODESPACE_NAME and CODESPACE_DOMAIN:
    host = f"{CODESPACE_NAME}-8000.{CODESPACE_DOMAIN}"
    if host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(host)

# ==================== SEGURIDAD (ANTI-BLOQUEOS 403) ====================
# IMPORTANTE: Configuración para evitar errores CSRF en Docker/Codespaces

# Confiar en el proxy HTTPS de GitHub
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Cookies seguras (Necesario porque Codespaces fuerza HTTPS)
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# Lista maestra de orígenes confiables (Incluye wildcards para cubrir todo)
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://localhost:8000",
    "https://127.0.0.1:8000",
    "https://*.github.dev",
    "https://*.app.github.dev",
    "https://*.preview.app.github.dev",
]

# Agregar explícitamente la URL dinámica del Codespace actual a los orígenes confiables
if CODESPACE_NAME and CODESPACE_DOMAIN:
    dynamic_origin = f"https://{CODESPACE_NAME}-8000.{CODESPACE_DOMAIN}"
    if dynamic_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(dynamic_origin)

X_FRAME_OPTIONS = "SAMEORIGIN"

# ==================== APLICACIONES ====================
INSTALLED_APPS = [
    # Apps nativas
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Librerías de terceros
    "rest_framework",
    "rest_framework.authtoken",
    "drf_spectacular",
    "corsheaders",
    # --- Arquitectura Limpia (Apps Locales) ---
    "infrastructure.persistence.apps.PersistenceConfig",
    "presentation",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "config.middleware.NoCacheMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "presentation" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ==================== BASE DE DATOS ====================
DATABASES = {
    "default": {
        "ENGINE": config("DB_ENGINE", default="django.db.backends.postgresql"),
        "NAME": config("DB_NAME", default="sgac_db"),
        "USER": config("DB_USER", default="sgac_user"),
        "PASSWORD": config("DB_PASSWORD", default="sgac_password"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
    }
}

# Modelo de Usuario Personalizado
AUTH_USER_MODEL = "persistence.CustomUser"

# ==================== CACHE & CELERY (REDIS) ====================
REDIS_URL = config("REDIS_URL", default="redis://localhost:6379/0")

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

# ==================== VALIDACIÓN DE PASSWORD ====================
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ==================== LOCALIZACIÓN ====================
LANGUAGE_CODE = "es-pe"
TIME_ZONE = "America/Lima"
USE_I18N = True
USE_TZ = True

# ==================== ESTÁTICOS Y MEDIA ====================
STATIC_URL = "/static/"
MEDIA_URL = "/media/"

STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT = BASE_DIR / "media"

STATICFILES_DIRS = [
    BASE_DIR / "presentation" / "static",
]

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ==================== DRF & API ====================
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "SGAC API",
    "DESCRIPTION": "Sistema de Gestión Académica Complementario",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# ==================== CORS ====================
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CORS_ALLOW_CREDENTIALS = True

# ==================== LOGGING ====================
LOG_DIR = BASE_DIR / "logs"
os.makedirs(LOG_DIR, exist_ok=True)

DISABLE_FILE_LOGGING = os.getenv("DISABLE_FILE_LOGGING") == "1"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        **(
            {}
            if DISABLE_FILE_LOGGING
            else {
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": LOG_DIR / "sgac.log",
                    "maxBytes": 1024 * 1024 * 5,
                    "backupCount": 5,
                    "formatter": "verbose",
                }
            }
        ),
    },
    "root": {
        "handlers": ["console"] if DISABLE_FILE_LOGGING else ["console", "file"],
        "level": "INFO",
    },
}

if os.getenv("PYTEST_CURRENT_TEST"):
    LOGGING_CONFIG = None

# ==================== UI HELPERS ====================
MESSAGE_TAGS = {
    messages.DEBUG: "secondary",
    messages.INFO: "info",
    messages.SUCCESS: "success",
    messages.WARNING: "warning",
    messages.ERROR: "danger",
}

LOGIN_URL = 'presentation:login'
LOGOUT_REDIRECT_URL = 'presentation:login'

