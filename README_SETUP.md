# SGAC - Guía de Setup para el Equipo

## 📋 Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:

- [Docker Engine](https://docs.docker.com/engine/install/)
- [Docker Compose (v2 o superior)](https://docs.docker.com/compose/install/)
- [Git](https://git-scm.com/downloads)

Verifica tus versiones:
```bash
docker --version
docker compose version

## 🚀 Primeros Pasos

### 1. Clonar el repositorio
```bash
git clone https://github.com/j-h-o-s-e-p/sgac.git
cd sgac
```

### 2. Configurar variables de entorno
```bash
cp .env.example .env
# El archivo .env ya tiene valores por defecto para desarrollo
```

### 3. Construir y levantar los contenedores
```bash
docker compose up -d --build
```

Esto levantará:
- PostgreSQL (puerto 5432)
- Redis (puerto 6379)
- Django Web (puerto 8000)
- Celery Worker

### 4. Ejecutar migraciones
```bash
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
```

### 5. Crear superusuario
```bash
docker compose exec web python manage.py createsuperuser
```

### 6. Acceder a la aplicación
- API Base: http://localhost:8000
- Admin Panel: http://localhost:8000/admin
- API Docs (Swagger): http://localhost:8000/api/schema/swagger-ui/

## 📂 Estructura del Proyecto
```
sgac/
├── config/              # Configuración Django
├── presentation/        # Capa de Presentación (Controllers, Serializers)
├── application/         # Capa de Aplicación (Services, DTOs)
├── domain/             # Capa de Dominio (Agregados, Entidades, VOs)
├── infrastructure/      # Capa de Infraestructura (Repositories, External Services)
├── shared/             # Código compartido
└── tests/              # Tests unitarios e integración
```

## 🌿 Estrategia de Ramas
```
main (producción)
  └── develop (desarrollo)
      ├── feature/identity-authentication
      ├── feature/academic-structure
      ├── feature/lab-enrollment
      ├── feature/academic-performance
      └── feature/reporting-dashboards
```

### Crear tu rama de trabajo
```bash
git checkout develop
git pull origin develop
git checkout -b feature/tu-contexto
```

## 🛠️ Comandos Útiles

### Ver logs en tiempo real
```bash
docker compose logs -f web
```

### Ejecutar tests
```bash
docker compose exec web pytest
```

### Acceder al shell de Django
```bash
docker compose exec web python manage.py shell
```

### Ejecutar comandos de manage.py
```bash
docker compose exec web python manage.py [comando]
```

### Parar los contenedores
```bash
docker compose down
```

### Reiniciar todo desde cero
```bash
docker compose down -v
docker compose up -d --build
docker compose exec web python manage.py migrate
```

## 📏 Convenciones de Código

- **Lenguaje:** Python 3.11
- **Estilo:** PEP 8
- **Formateador:** black
- **Linter:** flake8
- **Imports:** isort

### Antes de hacer commit
```bash
# Formatear código
docker compose exec web black .

# Verificar estilo
docker compose exec web flake8

# Ordenar imports
docker compose exec web isort .
```

## 🔄 Flujo de Trabajo

1. **Crear rama desde develop**
2. **Desarrollar feature**
3. **Hacer commits descriptivos**
4. **Push a tu rama**
5. **Crear Pull Request a develop**
6. **Code Review**
7. **Merge a develop**

### Formato de commits
```
[CONTEXTO] Descripción breve

- Cambio detallado 1
- Cambio detallado 2

Ejemplo:
[IDENTITY] Implementar login y activación de cuenta

- Crear User aggregate con validaciones
- Implementar UserApplicationService
- Crear endpoints de autenticación
```

## 🧪 Testing

### Ejecutar todos los tests
```bash
docker compose exec web pytest
```

### Ejecutar tests con cobertura
```bash
docker compose exec web pytest --cov
```

### Ejecutar tests específicos
```bash
docker compose exec web pytest tests/unit/domain/test_user.py
```

## 🐛 Troubleshooting

### Error de conexión a la BD
```bash
docker compose down
docker compose up -d db
# Esperar unos segundos
docker compose up -d web
```

### Limpiar caché de Python
```bash
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete
```

### Resetear la base de datos
```bash
docker compose down -v
docker compose up -d
docker compose exec web python manage.py migrate
```

## 💡 Notas Técnicas

### Usa siempre el comando moderno:
```bash
docker compose ...
```
### Antes de apagar tu PC, detén los contenedores:
```bash
docker compose down
```
### Si clonas el proyecto en otra máquina:
```bash
docker compose down -v --remove-orphans
docker compose up -d --build
```
### Todos los servicios usan volúmenes nombrados, por lo que el entorno puede recrearse sin conflictos.

## 📞 Contacto

Para dudas o problemas, crear un issue en GitHub o contactar al arquitecto del proyecto.
