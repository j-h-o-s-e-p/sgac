# 🧪 Guía de Testing - SGAC

Este documento explica cómo ejecutar todos los tipos de pruebas implementadas en el proyecto.

## 📦 Instalación de Dependencias

```bash
pip install -r requirements-dev.txt
```

## 🎯 Tipos de Tests

### 1️⃣ Tests Unitarios

Prueban componentes aislados (modelos, funciones, lógica de negocio).

```bash
# Todos los tests unitarios
pytest tests/unit/ -v

# Un archivo específico
pytest tests/unit/models/test_user_model.py -v

# Un test específico
pytest tests/unit/models/test_enrollment_model.py::TestStudentEnrollmentModel::test_calculate_final_grade_with_multiple_evaluations -v
```

### 2️⃣ Tests de Integración

Prueban flujos completos entre múltiples componentes.

```bash
pytest tests/integration/ -v
```

### 3️⃣ Tests Funcionales (E2E con Selenium)

Prueban la interfaz completa simulando un usuario real.

**Requisitos previos:**
- Chrome/Chromium instalado
- ChromeDriver (se instala automáticamente con selenium)

```bash
# Todos los tests de Selenium
pytest tests/functional/ -m selenium -v

# Solo un test específico
pytest tests/functional/test_login_selenium.py::TestLoginFlowSelenium::test_successful_student_login_and_redirect -v

# Excluir tests lentos
pytest tests/functional/ -m "selenium and not slow" -v
```

**Instalación de Chrome (Ubuntu/Debian):**
```bash
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update && sudo apt install -y google-chrome-stable
```

### 4️⃣ Tests de Rendimiento (Locust)

Simulan carga de usuarios concurrentes.

```bash
# Con interfaz web (recomendado para desarrollo)
locust -f tests/performance/locustfile.py --host=http://localhost:8000

# Luego abrir: http://localhost:8089

# Sin interfaz (headless)
locust -f tests/performance/locustfile.py \
    --host=http://localhost:8000 \
    --users 100 \
    --spawn-rate 10 \
    --run-time 1m \
    --headless
```

**Escenarios de carga:**
- **Light Load:** 10-20 usuarios concurrentes
- **Normal Load:** 50-100 usuarios concurrentes
- **Stress Test:** 200+ usuarios concurrentes

## 📊 Cobertura de Código

```bash
# Generar reporte de cobertura
pytest --cov=infrastructure.persistence.models --cov=application.services --cov-report=html

# Ver reporte en navegador
firefox htmlcov/index.html  # o chrome/chromium
```

## 🔍 Análisis de Calidad

### Black (Formateo automático)

```bash
# Verificar formato
black --check .

# Aplicar formato
black .
```

### Flake8 (Linter)

```bash
flake8 . --max-line-length=120 --exclude=migrations,venv
```

### Bandit (Seguridad)

```bash
# Análisis completo
bandit -r . -x ./tests,./venv

# Generar reporte JSON
bandit -r . -x ./tests,./venv --format json -o bandit-report.json
```

## 🚀 Ejecutar Todo (CI/CD Local)

```bash
# Script completo de validación (similar al pipeline)
./scripts/run_all_tests.sh
```

O manualmente:

```bash
# 1. Calidad de código
black --check .
flake8 . --max-line-length=120

# 2. Seguridad
bandit -r . -x ./tests,./venv

# 3. Tests unitarios + integración
pytest tests/unit/ tests/integration/ -v --cov=.

# 4. Tests E2E (opcional)
pytest tests/functional/ -m selenium -v

# 5. Performance (opcional, requiere servidor corriendo)
locust -f tests/performance/locustfile.py --host=http://localhost:8000 --headless --users 50 --run-time 30s
```

## 📝 Convenciones

### Marcadores de Pytest

- `@pytest.mark.unit` - Tests unitarios
- `@pytest.mark.integration` - Tests de integración
- `@pytest.mark.selenium` - Tests E2E con Selenium
- `@pytest.mark.slow` - Tests que toman más tiempo

### Estructura de Directorios

```
tests/
├── unit/                  # Tests unitarios
│   ├── models/           # Tests de modelos
│   └── services/         # Tests de servicios
├── integration/          # Tests de integración
├── functional/           # Tests E2E (Selenium)
├── performance/          # Tests de carga (Locust)
├── factories.py          # Factory Boy factories
└── conftest.py           # Configuración compartida
```

## 🐛 Debugging

```bash
# Ejecutar con salida detallada
pytest -vv -s

# Ejecutar solo tests que fallaron la última vez
pytest --lf

# Detener en el primer error
pytest -x

# Modo de debugging interactivo
pytest --pdb
```

## 🔧 Configuración de IDE

### VS Code

Agregar a `.vscode/settings.json`:

```json
{
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.pytestArgs": [
        "tests",
        "-v"
    ]
}
```

### PyCharm

1. Settings → Tools → Python Integrated Tools
2. Default test runner: pytest
3. Run → Edit Configurations → Add pytest configuration

## 📚 Referencias

- [Pytest Documentation](https://docs.pytest.org/)
- [Factory Boy](https://factoryboy.readthedocs.io/)
- [Selenium Python](https://selenium-python.readthedocs.io/)
- [Locust Documentation](https://docs.locust.io/)