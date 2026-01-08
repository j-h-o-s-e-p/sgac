import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from datetime import datetime

# Modelos solo para get_object_or_404 puntuales
from infrastructure.persistence.models import Course, CourseGroup

# Servicio
from application.services.professor_services import ProfessorService

_service = ProfessorService()

# ==================== VISTAS PRINCIPALES ====================


@login_required
def my_courses(request):
    """Lista de cursos asignados (Teoría y Lab)"""
    if request.user.user_role != "PROFESOR":
        return redirect("presentation:login")

    cards = _service.get_professor_courses_cards(request.user)
    return render(request, "professor/my_courses.html", {"unified_cards": cards})


@login_required
def dashboard(request):
    """Panel principal de estadísticas"""
    if request.user.user_role != "PROFESOR":
        return redirect("presentation:login")

    context = _service.get_dashboard_stats(request.user)
    return render(request, "professor/dashboard.html", context)


@login_required
def schedule(request):
    """Horario semanal"""
    if request.user.user_role != "PROFESOR":
        return redirect("presentation:login")

    context = _service.get_professor_schedule(request.user)
    return render(request, "professor/schedule.html", context)


# ==================== ASISTENCIA ====================


@login_required
def attendance(request):
    """Menú para elegir curso y tomar asistencia"""
    # Reutilizo cards de my_courses
    return my_courses(request)


@login_required
def record_attendance(request, group_id):
    """Interfaz principal de toma de asistencia"""
    if request.user.user_role != "PROFESOR":
        return redirect("presentation:login")

    # 1. Preparar datos desde el servicio
    date_param = request.GET.get("date")
    context = _service.get_attendance_session_data(request.user, group_id, date_param)

    if context.get("error"):
        messages.error(request, context["error"])
        return redirect("presentation:professor_dashboard")

    # 2. Procesar Guardado (POST)
    if request.method == "POST":
        session = context["current_session"]
        if session and context["is_editable"]:
            success = _service.save_attendance_process(
                request.user,
                group_id,
                session["date"],
                session["number"],
                request.POST,
                request.META.get("REMOTE_ADDR"),
            )
            if success:
                messages.success(request, "Asistencia guardada correctamente.")
            else:
                messages.error(request, "Error al guardar.")

            return redirect(f"{request.path}?date={session['date']}")
        else:
            messages.error(request, "No se puede editar esta sesión.")

    return render(request, "professor/record_attendance.html", context)


@login_required
def attendance_report(request, group_id):
    """Reporte matricial de asistencia y exportación Excel"""
    if request.user.user_role != "PROFESOR":
        return redirect("presentation:login")

    data = _service.get_attendance_report_matrix(request.user, group_id)
    if not data:
        return redirect("presentation:professor_dashboard")

    # Exportación Excel
    if request.GET.get("export") == "excel":
        wb = _service.generate_attendance_excel(
            data["group"], data["sessions"], data["matrix"]
        )
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        filename = f"Asistencia_{data['group'].course.course_code}.xlsx"
        response["Content-Disposition"] = f"attachment; filename={filename}"
        wb.save(response)
        return response

    return render(request, "professor/attendance_report.html", data)


# ==================== NOTAS ====================


@login_required
def grades(request):
    """Menú selección de curso para notas"""
    return my_courses(request)


@login_required
def consolidated_grades(request, group_id):
    """Matriz de notas por unidad"""
    if request.user.user_role != "PROFESOR":
        return redirect("presentation:login")

    # 1. Obtener datos
    context = _service.get_grades_consolidation(request.user, group_id)
    if not context:
        return redirect("presentation:professor_dashboard")

    # 2. Guardar Notas (POST)
    if request.method == "POST":
        unit = int(request.POST.get("unit_number"))
        saved, errors = _service.save_grades_batch(
            context["course"], unit, request.POST, request.user
        )

        if errors:
            messages.warning(
                request, f"Guardados: {saved}. Errores: {'; '.join(errors[:3])}"
            )
        else:
            messages.success(request, f"Notas Unidad {unit} guardadas ({saved}).")

        return redirect(request.path)

    return render(request, "professor/consolidated_grades.html", context)


@login_required
def upload_grades_csv(request, course_id):
    """Procesamiento de archivo CSV"""
    if request.user.user_role != "PROFESOR":
        return redirect("presentation:login")

    if request.method == "POST" and request.FILES.get("csv_file"):
        course = get_object_or_404(Course, course_id=course_id)
        unit = int(request.POST.get("unit_number", 1))

        try:
            success, errors = _service.process_csv_grades(
                request.FILES["csv_file"], course, unit, request.user
            )
            if errors:
                messages.warning(
                    request, f"Cargados: {success}. Errores: {len(errors)}"
                )
            else:
                messages.success(request, f"Éxito: {success} notas cargadas.")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

    # Redirige atrás
    return redirect(
        request.META.get("HTTP_REFERER", "presentation:professor_dashboard")
    )


# ==================== UTILIDADES ====================


@login_required
def upload_syllabus(request, course_id):
    """Subida de sílabo PDF"""
    if request.user.user_role != "PROFESOR":
        return redirect("presentation:login")

    if request.method == "POST" and request.FILES.get("syllabus_pdf"):
        try:
            _service.upload_syllabus(
                course_id, request.user, request.FILES["syllabus_pdf"]
            )
            messages.success(request, "Sílabo actualizado.")
        except PermissionError:
            messages.error(request, "No tienes permiso.")
        except Exception as e:
            messages.error(request, f"Error: {e}")

    return redirect("presentation:professor_my_courses")


@login_required
def statistics(request):
    """Estadísticas detalladas"""
    if request.user.user_role != "PROFESOR":
        return redirect("presentation:login")
    context = _service.get_statistics_context(request.user)
    return render(request, "professor/statistics.html", context or {"no_data": True})


@login_required
def get_course_progress_api(request, group_id):
    """API JSON para modal de línea de tiempo"""
    data = _service.get_group_syllabus_details(group_id)
    return JsonResponse(
        data if data else {"error": "No encontrado"}, status=200 if data else 404
    )

# ==================== RESERVAS DE AULAS ====================


@login_required
def classroom_reservation(request):
    """Vista principal de reservas de aulas para profesores"""
    if request.user.user_role != "PROFESOR":
        return redirect("presentation:login")
    
    # Obtener reservas activas e historial
    active_reservations = _service.get_professor_reservations(request.user, include_history=False)
    history = _service.get_professor_reservations(request.user, include_history=True)[:20]
    
    # Estadísticas rápidas
    from infrastructure.persistence.models import ClassroomReservation
    stats = {
        'total': ClassroomReservation.objects.filter(professor=request.user).count(),
        'pending': ClassroomReservation.objects.filter(professor=request.user, status='PENDIENTE').count(),
        'approved': ClassroomReservation.objects.filter(professor=request.user, status='APROBADA').count(),
    }
    
    context = {
        'active_reservations': active_reservations,
        'history': history,
        'stats': stats,
    }
    
    return render(request, "professor/classroom_reservation.html", context)


@login_required
def get_available_classrooms_api(request):
    """API para obtener aulas disponibles en una fecha/hora específica"""
    if request.user.user_role != "PROFESOR":
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    try:
        # Parsear parámetros
        date_str = request.GET.get('date')
        start_str = request.GET.get('start_time')
        end_str = request.GET.get('end_time')
        
        if not all([date_str, start_str, end_str]):
            return JsonResponse({'error': 'Parámetros incompletos'}, status=400)
        
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_time = datetime.strptime(start_str, '%H:%M').time()
        end_time = datetime.strptime(end_str, '%H:%M').time()
        
        # Obtener aulas disponibles
        available = _service.get_available_classrooms_for_reservation(
            date_obj, start_time, end_time
        )
        
        # Formatear respuesta
        classrooms_data = [
            {
                'id': str(c.classroom_id),
                'code': c.code,
                'name': c.name,
                'type': c.get_classroom_type_display(),
                'capacity': c.capacity,
                'location': c.location,
            }
            for c in available
        ]
        
        return JsonResponse({
            'success': True,
            'classrooms': classrooms_data,
            'count': len(classrooms_data)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def create_reservation_api(request):
    """API para crear una nueva reserva"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    if request.user.user_role != "PROFESOR":
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    try:
        data = json.loads(request.body)
        
        # Parsear datos
        classroom_id = data.get('classroom_id')
        date_obj = datetime.strptime(data.get('date'), '%Y-%m-%d').date()
        start_time = datetime.strptime(data.get('start_time'), '%H:%M').time()
        end_time = datetime.strptime(data.get('end_time'), '%H:%M').time()
        purpose = data.get('purpose', '').strip()
        
        if not purpose:
            return JsonResponse({'error': 'El motivo es obligatorio'}, status=400)
        
        # Crear reserva
        result = _service.create_classroom_reservation(
            request.user,
            classroom_id,
            date_obj,
            start_time,
            end_time,
            purpose
        )
        
        if result['success']:
            messages.success(request, result['message'])
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({'success': False, 'errors': [str(e)]}, status=500)


@login_required
def cancel_reservation_api(request):
    """API para cancelar una reserva"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    if request.user.user_role != "PROFESOR":
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    try:
        data = json.loads(request.body)
        reservation_id = data.get('reservation_id')
        
        result = _service.cancel_reservation(reservation_id, request.user)
        
        if result['success']:
            messages.success(request, result['message'])
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)