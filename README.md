# SGAC - Sistema de Gestión Académica Complementario

Sistema de gestión académica basado en Domain-Driven Design (DDD) para la administración de cursos, laboratorios, notas, asistencia y reportes académicos.

## 🏗️ Arquitectura

El proyecto sigue una arquitectura en capas basada en DDD:
```
sgac/
├── presentation/        # Capa de Presentación (API REST)
├── application/         # Capa de Aplicación (Casos de uso)
├── domain/             # Capa de Dominio (Lógica de negocio)
├── infrastructure/      # Capa de Infraestructura (BD, Servicios externos)
└── shared/             # Código compartido
```

## 🚀 Quick Start

### Requisitos
- Docker y Docker Compose

### Instalación
```bash
# 1. Clonar el repositorio
git clone https://github.com/j-h-o-s-e-p/sgac.git
cd sgac

# 2. Copiar variables de entorno
cp .env.example .env

# 3. Levantar servicios
docker-compose up -d --build

# 4. Crear superusuario
docker-compose exec web python manage.py createsuperuser

# 5. Acceder
# Admin: http://localhost:8000/admin
# API Docs: http://localhost:8000/api/schema/swagger-ui/
```

Para más detalles, ver [README_SETUP.md](README_SETUP.md)

## 📋 Contextos DDD

El sistema está dividido en 5 bounded contexts:

1. **Identity & Access Management** - Autenticación y usuarios
2. **Academic Structure** - Cursos, grupos, horarios, sílabos
3. **Laboratory Enrollment** - Postulación y asignación de laboratorios
4. **Academic Performance** - Notas, asistencia, exámenes sustitutorios
5. **Reporting & Analytics** - Dashboards y reportes

## 🛠️ Stack Tecnológico

- **Backend:** Django 4.2 + Django REST Framework
- **Base de Datos:** PostgreSQL 15
- **Cache/Eventos:** Redis 7
- **Task Queue:** Celery
- **Containerización:** Docker + Docker Compose
- **Testing:** pytest
- **API Docs:** drf-spectacular (OpenAPI/Swagger)

## 🌿 Workflow de Desarrollo
```
main (producción)
  └── develop (desarrollo)
      ├── feature/identity-authentication
      ├── feature/academic-structure
      ├── feature/lab-enrollment
      ├── feature/academic-performance
      └── feature/reporting-dashboards
```

## 📞 Contacto

Para dudas o issues, contactar al equipo de desarrollo.

## 📄 Licencia

[Definir licencia]
