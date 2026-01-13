import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

# Capa de Aplicación: Único punto de contacto para lógica de negocio
from application.services.student_services import StudentService


def student_required(view_func):
    """Decorador: Asegura que el usuario sea un alumno autenticado."""

    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.user_role != "ALUMNO":
            messages.error(request, "No tienes permisos para acceder a esta página.")
            return redirect("presentation:login")
        return view_func(request, *args, **kwargs)

    return _wrapped_view


# -----------------------------------------------------------------------------
# VISTAS PRINCIPALES (DASHBOARD Y GESTIÓN)
# -----------------------------------------------------------------------------


@student_required
def dashboard(request):
    """Panel principal con resumen académico."""
    context = StudentService.get_dashboard_stats(request.user)
    return render(request, "student/dashboard.html", context)


@student_required
def schedule(request):
    """Vista del horario semanal de clases y laboratorios."""
    context = StudentService.get_student_schedule(request.user)
    return render(request, "student/schedule.html", context)


@student_required
def grades(request):
    """Vista de notas consolidadas por curso y unidad."""
    courses_data = StudentService.get_grades_summary(request.user)
    return render(request, "student/grades.html", {"courses_data": courses_data})


@student_required
def attendance_list(request):
    """Listado resumen de asistencias por curso."""
    attendance_data = StudentService.get_attendance_summary(request.user)
    return render(
        request, "student/attendance_list.html", {"attendance_data": attendance_data}
    )


# -----------------------------------------------------------------------------
# GESTIÓN DE MATRÍCULA DE LABORATORIOS
# -----------------------------------------------------------------------------


@student_required
def lab_enrollment(request):
    """
    Vista principal de inscripción de laboratorios.
    Orquesta campañas activas, laboratorios ya inscritos y postulaciones pendientes.
    """
    # 1. Campañas activas disponibles para el alumno
    campaigns_data = StudentService.get_available_lab_campaigns(request.user)

    # 2. Laboratorios ya asignados y confirmados
    enrolled_labs = StudentService.get_enrolled_labs(request.user)

    # 3. Postulaciones en proceso
    postulations = StudentService.get_student_postulations(request.user)

    context = {
        "campaigns_data": campaigns_data,
        "enrolled_labs": enrolled_labs,
        "postulations": postulations,
    }
    return render(request, "student/lab_enrollment.html", context)


@student_required
@require_POST
def postulate_to_lab(request):
    """
    API (JSON): Procesa la postulación de un alumno a un grupo de laboratorio.
    """
    try:
        data = json.loads(request.body)
        campaign_id = data.get("campaign_id")
        lab_id = data.get("lab_id")

        if not campaign_id or not lab_id:
            return JsonResponse(
                {"success": False, "errors": ["Datos incompletos"]}, status=400
            )

        # Delegamos toda la lógica de validación e inserción al servicio
        result = StudentService.postulate_to_lab(
            student=request.user, campaign_id=campaign_id, lab_id=lab_id
        )

        return JsonResponse(result)

    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "errors": ["Formato de datos inválido"]}, status=400
        )
    except Exception as e:
        return JsonResponse(
            {"success": False, "errors": [f"Error del servidor: {str(e)}"]}, status=500
        )


@student_required
def get_lab_details(request, lab_id):
    """
    API (JSON): Obtiene detalles de un laboratorio para el modal de confirmación.
    REFACTORIZADO: Ya no accede a modelos directamente.
    """
    try:
        # El servicio se encarga de buscar el lab, formatear la data
        # y verificar conflictos específicos para este usuario.
        data = StudentService.get_lab_details_dto(lab_id, request.user)
        return JsonResponse(data)

    except Exception as e:
        # Captura genérica, idealmente el servicio maneja sus excepciones y retorna dicts de error
        return JsonResponse({"success": False, "error": str(e)}, status=500)


# -----------------------------------------------------------------------------
# VISTAS DE DETALLE (SÍLABOS Y ASISTENCIA)
# -----------------------------------------------------------------------------


@student_required
def syllabus_list(request):
    """Listado de cursos con sílabos disponibles."""
    courses_with_syllabus = StudentService.get_syllabus_list(request.user)
    return render(
        request,
        "student/syllabus_list.html",
        {"courses_with_syllabus": courses_with_syllabus},
    )


@student_required
def syllabus_detail(request, course_id):
    """Detalle del avance de un sílabo específico."""
    result = StudentService.get_syllabus_detail(request.user, course_id)

    # Manejo de errores de negocio retornados por el servicio
    if result.get("error") == "not_enrolled":
        messages.error(request, "No estás matriculado en este curso.")
        return redirect("presentation:student_syllabus_list")
    elif result.get("error") == "no_syllabus":
        messages.warning(request, "Este curso aún no tiene sílabo cargado.")
        return redirect("presentation:student_syllabus_list")

    return render(request, "student/syllabus_detail.html", result)


@student_required
def attendance_detail(request, course_id):
    """Detalle de asistencia clase por clase."""
    context = StudentService.get_attendance_detail(request.user, course_id)

    if not context:
        messages.error(request, "No estás matriculado en este curso o hubo un error.")
        return redirect("presentation:student_attendance_list")

    return render(request, "student/attendance_detail.html", context)
