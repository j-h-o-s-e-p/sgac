import json
from datetime import time
from django.shortcuts import redirect
from django.contrib import messages
from django.views.generic import TemplateView, View
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

# Capa de Infraestructura / Persistencia (Solo para lectura en GETs complejos)
from infrastructure.persistence.models import (
    LaboratoryGroup,
    Classroom,
    CustomUser,
    ExternalProfessor,
    CourseGroup,
)

# Capa de Aplicación (Lógica de Negocio)
from application.services.secretaria_services import SecretariaService

# Mixins de Seguridad
from .mixins import SecretariaRequiredMixin


class LabManagementView(SecretariaRequiredMixin, TemplateView):
    """
    Vista principal: Dashboard de Gestión de Laboratorios.
    Orquesta la información de cursos, cupos y estado de campañas.
    """

    template_name = "secretaria/secretaria_lab_management.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 1. Obtener cursos base
        courses_with_lab = SecretariaService.get_courses_with_lab()
        courses_data = []

        # 2. Construir DTOs para la vista (Idealmente esto iría en un método del servicio,
        #    pero es aceptable aquí para orquestación de presentación).
        for course in courses_with_lab:
            # Métricas del curso
            count = SecretariaService.get_course_enrollment_count(course.course_id)
            needed = SecretariaService.calculate_lab_groups_needed(count)

            # Datos existentes (Lectura directa permitida en presentación para QuerySets)
            existing = LaboratoryGroup.objects.filter(course=course)

            # IDs de profesores teóricos para sugerirlos primero en el select
            theory_ids = list(
                CourseGroup.objects.filter(
                    course=course, professor__isnull=False
                ).values_list("professor_id", flat=True)
            )

            # Validaciones de negocio
            can_enable_check = SecretariaService.can_enable_enrollment(course.course_id)
            campaign_status = SecretariaService.get_campaign_status(course.course_id)

            courses_data.append(
                {
                    "course": course,
                    "enrollment_count": count,
                    "labs_needed": needed,
                    "existing_labs": existing,
                    "has_all_labs": existing.count() >= needed,
                    "theory_professors_ids": theory_ids,
                    "can_enable_enrollment": can_enable_check["can_enable"],
                    "total_capacity": can_enable_check["total_capacity"],
                    "campaign_status": campaign_status,
                }
            )

        # 3. Cargar catálogos para los formularios
        context["courses_data"] = courses_data
        context["classrooms"] = Classroom.objects.filter(
            is_active=True, classroom_type="LABORATORIO"
        )
        context["professors"] = CustomUser.objects.filter(
            user_role="PROFESOR", is_active=True
        )
        context["external_professors"] = ExternalProfessor.objects.all()

        return context


class CreateLabGroupView(SecretariaRequiredMixin, View):
    """Procesa la creación de un nuevo grupo de laboratorio."""

    def post(self, request):
        try:
            # Preparar datos de profesor externo si aplica
            ext_data = None
            if request.POST.get("use_external_professor") == "true":
                ext_data = {
                    "full_name": request.POST.get("external_prof_name"),
                    "email": request.POST.get("external_prof_email", ""),
                    "phone": "",
                    "specialization": "",
                }

            # Delegar al Servicio
            result = SecretariaService.create_lab_group(
                course_id=request.POST.get("course_id"),
                nomenclature=request.POST.get("nomenclature"),
                capacity=int(request.POST.get("capacity")),
                day=request.POST.get("day_of_week"),
                start=time.fromisoformat(request.POST.get("start_time")),
                end=time.fromisoformat(request.POST.get("end_time")),
                room_id=request.POST.get("room_id") or None,
                prof_id=request.POST.get("professor_id") or None,
                ext_prof_data=ext_data,
            )

            if result["success"]:
                messages.success(request, "Laboratorio creado exitosamente")
            else:
                for error in result["errors"]:
                    messages.error(request, error)

        except Exception as e:
            messages.error(request, f"Error interno: {str(e)}")

        return redirect("presentation:secretaria_lab_management")


class DeleteLabGroupView(SecretariaRequiredMixin, View):
    """Elimina un grupo de laboratorio."""

    def post(self, request, lab_id):
        # REFACTORIZADO: La lógica de validación (si hay campaña cerrada) se movió al servicio.
        result = SecretariaService.delete_lab_group(lab_id)

        if result["success"]:
            messages.success(request, result["message"])
        else:
            messages.error(request, result["error"])

        return redirect("presentation:secretaria_lab_management")


# ==================== APIS JSON (AJAX) ====================


class CheckScheduleConflictsView(SecretariaRequiredMixin, View):
    """API: Verifica conflictos de horario antes de guardar."""

    def post(self, request):
        try:
            data = json.loads(request.body)
            conflicts = SecretariaService.check_schedule_conflicts(
                course_id=data.get("course_id"),
                day=data.get("day_of_week"),
                start=time.fromisoformat(data.get("start_time")),
                end=time.fromisoformat(data.get("end_time")),
                room_id=data.get("room_id"),
                exclude_lab_id=data.get("exclude_lab_id"),
            )
            return JsonResponse(conflicts)
        except Exception as e:
            return JsonResponse(
                {"has_conflict": True, "messages": [f"Error de validación: {str(e)}"]},
                status=400,
            )


class GetAvailableClassroomsView(SecretariaRequiredMixin, View):
    """API: Obtiene salones disponibles para un horario dado."""

    def post(self, request):
        try:
            data = json.loads(request.body)
            classrooms = SecretariaService.get_available_classrooms(
                day=data.get("day_of_week"),
                start=time.fromisoformat(data.get("start_time")),
                end=time.fromisoformat(data.get("end_time")),
            )
            return JsonResponse(
                {
                    "success": True,
                    "classrooms": [
                        {
                            "id": str(c.classroom_id),
                            "code": c.name,
                            "name": c.name,
                            "capacity": c.capacity,
                        }
                        for c in classrooms
                    ],
                }
            )
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)


class GetCampaignStatusView(SecretariaRequiredMixin, View):
    """API: Obtiene estado actual de la campaña."""

    def get(self, request, course_id):
        status = SecretariaService.get_campaign_status(course_id)
        return JsonResponse(status)


class GetLabEnrolledStudentsView(SecretariaRequiredMixin, View):
    """API: Obtiene alumnos inscritos en un lab."""

    def get(self, request, lab_id):
        students = SecretariaService.get_lab_enrolled_students(lab_id)
        return JsonResponse({"students": students})


# ==================== GESTIÓN DE CAMPAÑA ====================


class EnableLabEnrollmentView(SecretariaRequiredMixin, View):
    """Acción: Habilita matricula de laboratorios."""

    def post(self, request, course_id):
        days = int(request.POST.get("days_duration", 7))
        result = SecretariaService.enable_lab_enrollment(course_id, days)

        if result["success"]:
            messages.success(request, f"Matricula habilitada por {days} días")
        else:
            for error in result["errors"]:
                messages.error(request, error)

        return redirect("presentation:secretaria_lab_management")


class CloseLabEnrollmentView(SecretariaRequiredMixin, View):
    """Acción: Cierra matricula"""

    def post(self, request, course_id):
        result = SecretariaService.close_lab_enrollment(course_id)

        if result["success"]:
            messages.success(
                request, "Matricula cerrada y alumnos asignados correctamente"
            )
        else:
            for error in result["errors"]:
                messages.error(request, error)

        return redirect("presentation:secretaria_lab_management")
