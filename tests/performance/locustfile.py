"""
Pruebas de rendimiento con Locust
Simula carga de usuarios concurrentes en el sistema
"""
from locust import HttpUser, task, between, SequentialTaskSet
import random


class StudentBehavior(SequentialTaskSet):
    """
    Comportamiento típico de un estudiante en el sistema.
    Simula el flujo: Login -> Dashboard -> Ver Notas -> Ver Asistencia
    """

    def on_start(self):
        """Se ejecuta una vez cuando el usuario virtual inicia"""
        self.login()

    def login(self):
        """Simula el login de un estudiante"""
        # Primero obtener el CSRF token
        response = self.client.get("/auth/login/")
        
        # Extraer CSRF token (simplificado)
        csrftoken = self.client.cookies.get('csrftoken', '')
        
        # Intentar login
        self.client.post(
            "/auth/login/",
            {
                "email": f"student{random.randint(1, 100)}@unsa.edu.pe",
                "password": "testpassword123"
            },
            headers={"X-CSRFToken": csrftoken},
            name="Login"
        )

    @task(1)
    def view_dashboard(self):
        """Visita el dashboard del estudiante"""
        self.client.get("/student/dashboard/", name="Dashboard")

    @task(2)
    def view_grades(self):
        """Consulta las notas"""
        self.client.get("/student/grades/", name="Mis Notas")

    @task(2)
    def view_attendance(self):
        """Consulta la asistencia"""
        self.client.get("/student/attendance/", name="Mi Asistencia")

    @task(1)
    def view_schedule(self):
        """Consulta el horario"""
        self.client.get("/student/schedule/", name="Mi Horario")

    @task(1)
    def view_syllabus_list(self):
        """Lista los sílabos disponibles"""
        self.client.get("/student/syllabus/", name="Sílabos")


class ProfessorBehavior(SequentialTaskSet):
    """
    Comportamiento típico de un profesor.
    Simula: Login -> Mis Cursos -> Registrar Asistencia
    """

    def on_start(self):
        self.login()

    def login(self):
        response = self.client.get("/auth/login/")
        csrftoken = self.client.cookies.get('csrftoken', '')
        
        self.client.post(
            "/auth/login/",
            {
                "email": f"professor{random.randint(1, 20)}@unsa.edu.pe",
                "password": "testpassword123"
            },
            headers={"X-CSRFToken": csrftoken},
            name="Professor Login"
        )

    @task(3)
    def view_my_courses(self):
        """Lista los cursos asignados"""
        self.client.get("/professor/my-courses/", name="Mis Cursos")

    @task(2)
    def view_course_statistics(self):
        """Ve estadísticas del curso"""
        # Simula ver estadísticas de un curso aleatorio
        course_id = random.randint(1, 10)
        self.client.get(
            f"/professor/statistics/?course_id={course_id}",
            name="Estadísticas Curso"
        )

    @task(1)
    def view_schedule(self):
        """Consulta su horario"""
        self.client.get("/professor/schedule/", name="Horario Profesor")


class StudentUser(HttpUser):
    """
    Usuario virtual que simula a un estudiante.
    """
    tasks = [StudentBehavior]
    wait_time = between(1, 3)  # Espera entre 1 y 3 segundos entre tareas
    weight = 3  # 75% de los usuarios serán estudiantes


class ProfessorUser(HttpUser):
    """
    Usuario virtual que simula a un profesor.
    """
    tasks = [ProfessorBehavior]
    wait_time = between(2, 5)  # Los profesores son más pausados
    weight = 1  # 25% de los usuarios serán profesores


class QuickLoadTest(HttpUser):
    """
    Test de carga simple: Solo consultas GET rápidas.
    Útil para medir capacidad máxima del servidor.
    """
    weight = 0  # Desactivado por defecto, activar manualmente si se necesita

    @task(1)
    def index(self):
        self.client.get("/")

    @task(3)
    def login_page(self):
        self.client.get("/auth/login/")

    @task(2)
    def static_resources(self):
        """Simula carga de recursos estáticos"""
        resources = [
            "/static/css/custom.css",
            "/static/js/main.js",
        ]
        for resource in resources:
            self.client.get(resource, name="/static/[resource]")

    wait_time = between(0.5, 2)


# ============ CONFIGURACIÓN DE ESCENARIOS ============

class StressTestScenario(HttpUser):
    """
    Escenario de prueba de estrés.
    Usuarios agresivos que hacen muchas peticiones rápidas.
    """
    tasks = [StudentBehavior, ProfessorBehavior]
    wait_time = between(0.1, 0.5)  # Muy rápido
    weight = 0  # Activar manualmente para stress testing


# ============ HOOKS DE EVENTOS ============

from locust import events

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Se ejecuta cuando inicia la prueba"""
    print("\n" + "="*50)
    print("🚀 INICIANDO PRUEBAS DE RENDIMIENTO")
    print("="*50 + "\n")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Se ejecuta cuando termina la prueba"""
    print("\n" + "="*50)
    print("✅ PRUEBAS DE RENDIMIENTO COMPLETADAS")
    print("="*50 + "\n")
    
    # Mostrar resumen
    stats = environment.stats
    print(f"Total de requests: {stats.total.num_requests}")
    print(f"Requests fallidas: {stats.total.num_failures}")
    print(f"Tiempo promedio de respuesta: {stats.total.avg_response_time:.2f}ms")
    print(f"RPS (requests per second): {stats.total.total_rps:.2f}")
    print()

@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """
    Se ejecuta después de cada request.
    Útil para logging o alertas personalizadas.
    """
    if exception:
        print(f"❌ Error en {name}: {exception}")
    elif response_time > 2000:  # Si tarda más de 2 segundos
        print(f"⚠️  Request lenta detectada: {name} ({response_time:.0f}ms)")