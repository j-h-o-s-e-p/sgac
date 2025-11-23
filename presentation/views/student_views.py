from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
# Importamos modelos necesarios 
from infrastructure.persistence.models import StudentEnrollment, Syllabus
# Importamos el servicio
from application.services.student_services import StudentService

# --- Para no repetir el if user_role) ---
def student_required(view_func):
    """Decorador para asegurar que solo alumnos accedan"""
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.user_role != 'ALUMNO':
            messages.error(request, 'No tienes permisos para acceder a esta página.')
            return redirect('presentation:login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# -----------------------------------------------------------------------------
# VISTAS PRINCIPALES 
# -----------------------------------------------------------------------------

@student_required
def dashboard(request):
    """Dashboard principal del alumno"""
    context = StudentService.get_dashboard_stats(request.user)
    return render(request, 'student/dashboard.html', context)

@student_required
def schedule(request):
    """Vista de horario del alumno"""
    context = StudentService.get_student_schedule(request.user)
    return render(request, 'student/schedule.html', context)

@student_required
def grades(request):
    """Vista de notas del alumno"""
    courses_data = StudentService.get_grades_summary(request.user)
    return render(request, 'student/grades.html', {'courses_data': courses_data})

@student_required
def lab_enrollment(request):
    """Vista de matrícula de laboratorios"""
    courses_with_labs, enrolled_labs = StudentService.get_lab_enrollment_options(request.user)
    context = {
        'courses_with_labs': courses_with_labs,
        'enrolled_labs': enrolled_labs,
    }
    return render(request, 'student/lab_enrollment.html', context)

@student_required
def attendance_list(request):
    """Lista de asistencia por curso"""
    attendance_data = StudentService.get_attendance_summary(request.user)
    return render(request, 'student/attendance_list.html', {'attendance_data': attendance_data})


# -----------------------------------------------------------------------------
# VISTAS DE DETALLE / SIMPLE 
# -----------------------------------------------------------------------------

@student_required
def syllabus_list(request):
    """Lista de sílabos disponibles"""
    enrollments = StudentEnrollment.objects.filter(
        student=request.user,
        status='ACTIVO',
        course__syllabus__isnull=False
    ).select_related('course', 'course__syllabus')
    
    courses_with_syllabus = []
    for enrollment in enrollments:
        syllabus = enrollment.course.syllabus
        courses_with_syllabus.append({
            'enrollment': enrollment,
            'course': enrollment.course,
            'syllabus': syllabus,
            'progress': syllabus.get_progress_percentage(),
        })
    
    return render(request, 'student/syllabus_list.html', {'courses_with_syllabus': courses_with_syllabus})

@student_required
def syllabus_detail(request, course_id):
    """Detalle del sílabo"""
    # Esta lógica es específica de validación de acceso, se puede quedar aquí o moverse al servicio
    try:
        enrollment = StudentEnrollment.objects.select_related(
            'course', 'course__syllabus'
        ).get(student=request.user, course__course_id=course_id, status='ACTIVO')
    except StudentEnrollment.DoesNotExist:
        messages.error(request, 'No estás matriculado en este curso.')
        return redirect('presentation:student_syllabus_list')
    
    try:
        syllabus = enrollment.course.syllabus
    except Syllabus.DoesNotExist: # Ajustado si Syllabus no se importa, usa model generico o try/except
        messages.warning(request, 'Este curso aún no tiene sílabo cargado.')
        return redirect('presentation:student_syllabus_list')
    
    sessions = syllabus.sessions.all().order_by('session_number')
    completed = sessions.filter(real_date__isnull=False).count()
    
    context = {
        'enrollment': enrollment,
        'course': enrollment.course,
        'syllabus': syllabus,
        'sessions': sessions,
        'total_sessions': sessions.count(),
        'completed_sessions': completed,
        'pending_sessions': sessions.count() - completed,
        'progress': syllabus.get_progress_percentage(),
    }
    return render(request, 'student/syllabus_detail.html', context)

@student_required
def attendance_detail(request, course_id):
    """Detalle de asistencia de un curso específico"""
    try:
        enrollment = StudentEnrollment.objects.select_related('course').get(
            student=request.user, course__course_id=course_id, status='ACTIVO'
        )
    except StudentEnrollment.DoesNotExist:
        messages.error(request, 'No estás matriculado en este curso.')
        return redirect('presentation:student_attendance_list')
    
    records = enrollment.attendance_records.all().order_by('session_number')
    total = records.count()
    present = records.filter(status='P').count()
    justified = records.filter(status='J').count()
    absent = records.filter(status='F').count()
    
    percentage = round(((present + justified) / total) * 100, 2) if total > 0 else 0
    
    # Simple lógica visual, puede quedarse aquí
    if percentage >= 70: status_class, status_text = 'success', 'Aprobado'
    elif percentage >= 30: status_class, status_text = 'warning', 'En Riesgo'
    else: status_class, status_text = 'danger', 'Crítico'
    
    context = {
        'enrollment': enrollment,
        'course': enrollment.course,
        'attendance_records': records,
        'total_sessions': total,
        'present_count': present,
        'justified_count': justified,
        'absent_count': absent,
        'percentage': percentage,
        'status_class': status_class,
        'status_text': status_text,
    }
    return render(request, 'student/attendance_detail.html', context)