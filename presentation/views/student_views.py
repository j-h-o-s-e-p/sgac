from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
# Solo importo el servicio, ya no necesito modelos aquí
from application.services.student_services import StudentService

def student_required(view_func):
    """Solo alumnos pueden pasar por aquí"""
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
    """Panel principal con resumen"""
    context = StudentService.get_dashboard_stats(request.user)
    return render(request, 'student/dashboard.html', context)

@student_required
def schedule(request):
    """Mi horario de clases y labs"""
    context = StudentService.get_student_schedule(request.user)
    return render(request, 'student/schedule.html', context)

@student_required
def grades(request):
    """Mis notas por unidad"""
    courses_data = StudentService.get_grades_summary(request.user)
    return render(request, 'student/grades.html', {'courses_data': courses_data})

@student_required
def lab_enrollment(request):
    """Donde elijo mis laboratorios"""
    courses_with_labs, enrolled_labs = StudentService.get_lab_enrollment_options(request.user)
    context = {
        'courses_with_labs': courses_with_labs,
        'enrolled_labs': enrolled_labs,
    }
    return render(request, 'student/lab_enrollment.html', context)

@student_required
def attendance_list(request):
    """Resumen de mis asistencias"""
    attendance_data = StudentService.get_attendance_summary(request.user)
    return render(request, 'student/attendance_list.html', {'attendance_data': attendance_data})


# -----------------------------------------------------------------------------
# VISTAS DE DETALLE
# -----------------------------------------------------------------------------

@student_required
def syllabus_list(request):
    """Veo qué cursos tienen sílabo"""
    courses_with_syllabus = StudentService.get_syllabus_list(request.user)
    return render(request, 'student/syllabus_list.html', {'courses_with_syllabus': courses_with_syllabus})

@student_required
def syllabus_detail(request, course_id):
    """Veo el avance tema por tema de un curso"""
    result = StudentService.get_syllabus_detail(request.user, course_id)
    
    # Manejo errores que me devuelve el servicio
    if result.get('error') == 'not_enrolled':
        messages.error(request, 'No estás matriculado en este curso.')
        return redirect('presentation:student_syllabus_list')
    elif result.get('error') == 'no_syllabus':
        messages.warning(request, 'Este curso aún no tiene sílabo cargado.')
        return redirect('presentation:student_syllabus_list')
        
    return render(request, 'student/syllabus_detail.html', result)

@student_required
def attendance_detail(request, course_id):
    """Veo fecha por fecha mis faltas en un curso"""
    context = StudentService.get_attendance_detail(request.user, course_id)
    
    if not context:
        messages.error(request, 'No estás matriculado en este curso.')
        return redirect('presentation:student_attendance_list')
    
    return render(request, 'student/attendance_detail.html', context)