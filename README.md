SGAC - Sistema de Gestión Académica Complementario
==================================================

Sistema integral de gestión académica diseñado para universidades, enfocado en la administración eficiente de la carga lectiva, laboratorios, asistencia y análisis de rendimiento académico mediante dashboards interactivos.

🏗️ Arquitectura
----------------

El proyecto sigue una arquitectura modular inspirada en Clean Architecture y Domain-Driven Design (DDD) para garantizar escalabilidad y mantenimiento:

```

sgac/
├── presentation/    # Capa de Interfaz (Vistas, Templates, Static, Serializers)
├── application/     # Capa de Aplicación (Servicios, Casos de Uso, DTOs)
├── domain/          # Capa de Dominio (Lógica de Negocio Pura)
├── infrastructure/  # Capa de Infraestructura (Modelos ORM, Repositorios, Comandos)
└── config/          # Configuración del Framework (Settings, URLs, WSGI/ASGI)

```

📋 Módulos del Sistema
----------------------

El sistema cuenta con 3 portales especializados y un panel administrativo central:

### 1\. Módulo de Secretaría (Administrativo)

-   Dashboard Ejecutivo: KPIs en tiempo real y gráficos de ocupación/rendimiento (Chart.js)

-   Gestión de Infraestructura: Administración de salones, aforos y tipos de aula

-   Gestión de Laboratorios: Creación dinámica de grupos prácticos con detección automática de conflictos de horario (AJAX)

-   Programación Académica: Asignación visual de horarios para grupos teóricos

-   Carga Masiva: Importación de alumnos matriculados vía CSV

-   Reportes: Generación de consolidados de notas en Excel

### 2\. Módulo de Profesor

-   Gestión de Cursos: Vista unificada de cursos de teoría y laboratorio asignados

-   Control de Asistencia: Registro diario con validación de fechas y control de avance de temas del sílabo

-   Registro de Notas: Sábana de notas dinámica con cálculos automáticos

-   Gestión de Sílabos: Carga, actualización y visualización de sílabos en PDF

-   Estadísticas Docentes: Análisis gráfico de rendimiento y asistencia de sus aulas

### 3\. Módulo de Estudiante

-   Mi Horario: Visualización semanal de clases (Teoría y Práctica)

-   Matrícula de Laboratorio: Sistema de postulación e inscripción a grupos prácticos

-   Seguimiento Académico: Consulta de notas, asistencia y descarga de sílabos

🛠️ Stack Tecnológico
---------------------

-   Backend: Python 3.11, Django 4.2

-   Base de Datos: PostgreSQL 15

-   Frontend: Django Templates, Bootstrap 5, JavaScript (ES6), Chart.js 4.4

-   Asincronía: Celery + Redis (para tareas en segundo plano y caché)

-   Containerización: Docker & Docker Compose

-   Calidad de Código: Black, Flake8, Isort

🚀 Quick Start (Resumen)
------------------------

Si ya tienes Docker instalado, puedes levantar el proyecto en minutos:

1.  Clonar repositorio:

    bash

    ```
    git clone https://github.com/j-h-o-s-e-p/sgac.git
    cd sgac
    ```

2.  Configurar entorno:

    bash
    
    ```
    cp .env.example .env
    ```

3.  Levantar contenedores:

    bash

    ```
    docker compose up -d --build
    ```

4.  Inicializar base de datos:

    bash

    ```
    docker compose exec web python manage.py migrate
    ```

5.  📦 Cargar Datos Iniciales (Seed):\
    El sistema incluye comandos personalizados para poblar la base de datos:

    Cargar Estructura Académica (Semestre, Cursos, Profesores):

    bash

    ```
    docker compose exec web python manage.py load_initial_data scripts/data/Curso_Profesor.csv
    ```

    Generar Asistencia Aleatoria (Opcional para Testing):

    bash

    ```
    docker compose exec web python manage.py seed_attendance
    ```

6.  Acceder:

    -   Web: `http://localhost:8000/login/`

    -   Admin: `http://localhost:8000/admin/`

    -   Swagger API: `http://localhost:8000/api/schema/swagger-ui/`

> Para la guía detallada de instalación, comandos de desarrollo y troubleshooting, revisa el archivo [README_SETUP.md](https://readme_setup.md/).

📄 Licencia
-----------

Este proyecto es de uso académico y privado.