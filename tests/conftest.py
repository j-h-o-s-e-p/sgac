# tests/conftest.py
import os
import sys
import django
from django.conf import settings

# Establecer variable ANTES de importar/configurar Django
os.environ['PYTEST_CURRENT_TEST'] = '1'
os.environ['DISABLE_FILE_LOGGING'] = '1'

def pytest_configure():
    """Configurar Django para tests"""
    
    # Verificar si Django ya está configurado
    if settings.configured:
        return
    
    # Configurar settings para tests
    settings.configure(
        DEBUG=False,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.admin',
            'django.contrib.sessions',
            'django.contrib.messages',
            'django.contrib.staticfiles',
            'rest_framework',
            'rest_framework.authtoken',
            'drf_spectacular',
            'corsheaders',
            'infrastructure.persistence',
            'presentation',
        ],
        MIDDLEWARE=[
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
        ],
        ROOT_URLCONF='config.urls',
        SECRET_KEY='test-secret-key-12345',
        USE_TZ=True,
        TIME_ZONE='UTC',
        
        # Deshabilitar logging
        LOGGING_CONFIG=None,
        
        # Configuración DRF para tests
        REST_FRAMEWORK={
            'DEFAULT_AUTHENTICATION_CLASSES': [
                'rest_framework.authentication.SessionAuthentication',
            ],
            'TEST_REQUEST_DEFAULT_FORMAT': 'json',
        },
        
        # AUTH_USER_MODEL debe coincidir con tu proyecto
        AUTH_USER_MODEL='persistence.CustomUser',
    )
    
    django.setup()


# Fixtures básicos para tests
import pytest
from django.test import Client

@pytest.fixture
def client():
    """Fixture para cliente de pruebas"""
    return Client()

@pytest.fixture
def admin_user(db):
    """Crear un usuario administrador"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_superuser(
        username='admin',
        email='admin@test.com',
        password='testpass123'
    )

@pytest.fixture
def regular_user(db):
    """Crear un usuario regular"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(
        username='user',
        email='user@test.com',
        password='testpass123'
    )

@pytest.fixture
def sample_student(db):
    """Fixture reutilizable: Un estudiante de ejemplo"""
    from tests.factories import StudentFactory
    return StudentFactory.create(
        first_name="Juan",
        last_name="Pérez",
        email="juan.perez@unsa.edu.pe"
    )

@pytest.fixture
def sample_course(db):
    """Fixture reutilizable: Un curso completo con evaluaciones"""
    from tests.factories import CourseFactory, EvaluationFactory
    from decimal import Decimal
    
    course = CourseFactory.create(
        course_code="IS101",
        course_name="Ingeniería de Software I"
    )
    
    # Crear estructura de evaluación estándar
    EvaluationFactory.create(course=course, name="Parcial", percentage=Decimal("30.00"))
    EvaluationFactory.create(course=course, name="Final", percentage=Decimal("40.00"))
    EvaluationFactory.create(course=course, name="Prácticas", percentage=Decimal("30.00"))
    
    return course