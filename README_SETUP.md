# SGAC - Guía de Setup para el Equipo

## 📋 Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:

- [Docker Engine](https://docs.docker.com/engine/install/)
- [Docker Compose (v2 o superior)](https://docs.docker.com/compose/install/)
- [Git](https://git-scm.com/downloads)

Verifica tus versiones:

Bash

```
docker --version
docker compose version
```

🚀 Primeros Pasos
-----------------

### 1\. Clonar el repositorio

Bash

```
git clone [https://github.com/j-h-o-s-e-p/sgac.git](https://github.com/j-h-o-s-e-p/sgac.git)
cd sgac
```

### 2\. Configurar variables de entorno

Bash

```
cp .env.example .env
# El archivo .env ya tiene valores por defecto para desarrollo local
```

### 3\. Construir y levantar los contenedores

Bash

```
docker compose up -d --build
```

Esto levantará:

-   **db:** PostgreSQL 15 (puerto 5432)

-   **redis:** Redis 7 (puerto 6379)

-   **web:** Django Web App (puerto 8000)

-   **worker:** Celery Worker (procesamiento asíncrono)

### 4\. Ejecutar migraciones

Bash

```
docker compose exec web python manage.py migrate
```

### 5\. Crear superusuario (Admin)

Bash

```
docker compose exec web python manage.py createsuperuser
```

### 6\. 📦 Poblado de Datos Iniciales (SEEDING)

Para no empezar con el sistema vacío, ejecuta estos comandos en orden:

**A. Cargar Cursos, Profesores y Grupos (desde CSV):** Este comando lee el archivo `scripts/data/Curso_Profesor.csv`, crea el semestre activo y estructura la base académica.

Bash

```
docker compose exec web python manage.py load_initial_data scripts/data/Curso_Profesor.csv
```

**B. Generar Asistencia Aleatoria (Opcional - Testing):** Genera registros de asistencia para el curso de Ingeniería de Software II (o el que indiques) para probar los gráficos.

Bash

```
docker compose exec web python manage.py seed_attendance
```

### 7\. Acceder a la aplicación

Una vez levantado, puedes acceder a los diferentes módulos:

-   **Login General:** http://localhost:8000/login/

-   **Panel de Secretaría:** http://localhost:8000/secretaria/dashboard/

-   **Panel de Profesor:** http://localhost:8000/professor/dashboard/

-   **Panel de Estudiante:** http://localhost:8000/student/dashboard/

-   **Admin Panel (Django):** http://localhost:8000/admin/

-   **API Docs (Swagger):** http://localhost:8000/api/schema/swagger-ui/

* * * * *

📂 Estructura del Proyecto (Clean Architecture + DDD)
-----------------------------------------------------

```
sgac/
├── config/              # Configuración del proyecto (Settings, Celery, URLs globales)
├── presentation/        # Capa de Presentación (Vistas, Templates, Static, URLs)
├── application/         # Capa de Aplicación (Servicios, Casos de Uso)
├── domain/              # Capa de Dominio (Modelos puros -aunque usamos modelos de Django en infra-)
├── infrastructure/      # Capa de Infraestructura (Modelos ORM, Repositorios, Comandos de Gestión)
│   └── persistence/     # Modelos de BD y scripts de carga (management/commands)
├── shared/              # Utilidades compartidas
└── tests/               # Tests unitarios e integración

```

🛠️ Comandos Útiles
-------------------

### Ver logs en tiempo real

Bash

```
docker compose logs -f web
```

### Ejecutar tests

Bash

```
docker compose exec web pytest
```

### Acceder al shell de Django

Bash

```
docker compose exec web python manage.py shell
```

### Reiniciar todo desde cero (Borrar BD y volver a crear)

¡Cuidado! Esto borra todos los datos.

Bash

```
docker compose down -v
docker compose up -d --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py load_initial_data scripts/data/Curso_Profesor.csv
```

📏 Convenciones de Código
-------------------------

-   **Estilo:** PEP 8

-   **Frontend:** Bootstrap 5 + Chart.js (Vistas renderizadas por Django Templates)

### Antes de hacer commit

Bash

```
# Formatear código (Black)
docker compose exec web black .

# Ordenar imports (Isort)
docker compose exec web isort .
```

🐛 Troubleshooting
------------------

### Error: "Relation does not exist"

Faltan correr las migraciones.

Bash

```
docker compose exec web python manage.py migrate
```

### Error: Gráficos vacíos en Dashboard

Asegúrate de haber ejecutado el comando de seed o tener alumnos matriculados con notas/asistencia.

Bash

```
docker compose exec web python manage.py seed_attendance
```

📞 Contacto
-----------

Para dudas sobre la arquitectura, contactar al equipo de desarrollo backend.