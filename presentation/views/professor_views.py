from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from infrastructure.persistence.models import (
    CourseGroup, LaboratoryGroup, StudentEnrollment,
    AttendanceRecord, GradeRecord, Evaluation
)
from datetime import date, datetime
from decimal import Decimal


@login_required
def dashboard(request):
    """Dashboard principal del profesor"""
    
    if request.user.user_role != 'PROFESOR':
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('presentation:login')
    
    # Obtener grupos que enseña
    course_groups = CourseGroup.objects.filter(
        professor=request.user
    ).select_related('course')
    
    lab_groups = LaboratoryGroup.objects.filter(
        professor=request.user
    ).select_related('course')
    
    # Estadísticas rápidas
    total_courses = course_groups.count() + lab_groups.count()
    
    context = {
        'course_groups': course_groups,
        'lab_groups': lab_groups,
        'total_courses': total_courses,
    }
    
    return render(request, 'professor/dashboard.html', context)


@login_required
def attendance(request):
    """Vista de asistencia del profesor"""
    
    if request.user.user_role != 'PROFESOR':
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('presentation:login')
    
    # Obtener grupos que enseña
    course_groups = CourseGroup.objects.filter(
        professor=request.user
    ).select_related('course')
    
    lab_groups = LaboratoryGroup.objects.filter(
        professor=request.user
    ).select_related('course')
    
    context = {
        'course_groups': course_groups,
        'lab_groups': lab_groups,
    }
    
    return render(request, 'professor/attendance.html', context)


@login_required
def record_attendance(request, group_id):
    """Registrar asistencia para un grupo"""
    
    if request.user.user_role != 'PROFESOR':
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('presentation:login')
    
    # Buscar si es grupo de curso o lab
    group = None
    group_type = None
    
    try:
        group = CourseGroup.objects.get(group_id=group_id, professor=request.user)
        group_type = 'course'
    except CourseGroup.DoesNotExist:
        try:
            group = LaboratoryGroup.objects.get(lab_id=group_id, professor=request.user)
            group_type = 'lab'
        except LaboratoryGroup.DoesNotExist:
            messages.error(request, 'Grupo no encontrado.')
            return redirect('presentation:professor_attendance')
    
    # Obtener estudiantes matriculados
    if group_type == 'course':
        enrollments = StudentEnrollment.objects.filter(
            course=group.course,
            group=group,
            status='ACTIVO'
        ).select_related('student')
    else:
        enrollments = StudentEnrollment.objects.filter(
            lab_assignment__lab_group=group,
            status='ACTIVO'
        ).select_related('student')
    
    if request.method == 'POST':
        session_number = request.POST.get('session_number')
        session_date = request.POST.get('session_date')
        
        if not session_number or not session_date:
            messages.error(request, 'Debes especificar el número de sesión y la fecha.')
            return redirect(request.path)
        
        session_number = int(session_number)
        session_date = datetime.strptime(session_date, '%Y-%m-%d').date()
        
        # Verificar que la fecha sea hoy
        if session_date != date.today():
            messages.error(request, 'Solo puedes registrar asistencia para el día de hoy.')
            return redirect(request.path)
        
        # Registrar asistencia para cada alumno
        for enrollment in enrollments:
            status = request.POST.get(f'status_{enrollment.enrollment_id}')
            
            if status:
                # Verificar si ya existe registro
                existing = AttendanceRecord.objects.filter(
                    enrollment=enrollment,
                    session_number=session_number
                ).first()
                
                if existing:
                    # Actualizar
                    existing.status = status
                    existing.save()
                else:
                    # Crear nuevo
                    AttendanceRecord.objects.create(
                        enrollment=enrollment,
                        session_number=session_number,
                        session_date=session_date,
                        status=status,
                        professor_ip=request.META.get('REMOTE_ADDR', '127.0.0.1'),
                        recorded_by=request.user
                    )
                
                # Recalcular porcentaje
                enrollment.calculate_attendance_percentage()
        
        messages.success(request, f'Asistencia de la sesión {session_number} registrada exitosamente.')
        return redirect('presentation:professor_attendance')
    
    context = {
        'group': group,
        'group_type': group_type,
        'enrollments': enrollments,
        'today': date.today(),
    }
    
    return render(request, 'professor/record_attendance.html', context)


@login_required
def grades(request):
    """Vista de notas del profesor"""
    
    if request.user.user_role != 'PROFESOR':
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('presentation:login')
    
    # Obtener cursos que enseña
    course_groups = CourseGroup.objects.filter(
        professor=request.user
    ).select_related('course').distinct()
    
    # Obtener cursos únicos
    courses = set([group.course for group in course_groups])
    
    context = {
        'courses': courses,
    }
    
    return render(request, 'professor/grades.html', context)


@login_required
def record_grades(request, course_id):
    """Registrar notas para un curso"""
    
    if request.user.user_role != 'PROFESOR':
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('presentation:login')
    
    # Verificar que el profesor enseña este curso
    course_groups = CourseGroup.objects.filter(
        course__course_id=course_id,
        professor=request.user
    ).select_related('course')
    
    if not course_groups.exists():
        messages.error(request, 'No tienes permisos para registrar notas en este curso.')
        return redirect('presentation:professor_grades')
    
    course = course_groups.first().course
    
    # Obtener evaluaciones del curso
    evaluations = Evaluation.objects.filter(course=course).order_by('unit', 'name')
    
    # Si se seleccionó una evaluación
    selected_evaluation_id = request.GET.get('evaluation')
    selected_evaluation = None
    enrollments_with_grades = []
    
    if selected_evaluation_id:
        selected_evaluation = get_object_or_404(Evaluation, evaluation_id=selected_evaluation_id)
        
        # Obtener todos los estudiantes del curso
        enrollments = StudentEnrollment.objects.filter(
            course=course,
            status='ACTIVO'
        ).select_related('student')
        
        # Obtener notas existentes
        existing_grades = GradeRecord.objects.filter(
            evaluation=selected_evaluation,
            enrollment__in=enrollments
        )
        
        grades_dict = {grade.enrollment.enrollment_id: grade for grade in existing_grades}
        
        for enrollment in enrollments:
            enrollments_with_grades.append({
                'enrollment': enrollment,
                'grade': grades_dict.get(enrollment.enrollment_id),
            })
    
    if request.method == 'POST' and selected_evaluation:
        # Registrar notas
        for enrollment in enrollments:
            raw_score = request.POST.get(f'grade_{enrollment.enrollment_id}')
            
            if raw_score:
                try:
                    raw_score = Decimal(raw_score)
                    
                    # Validar rango
                    if raw_score < 0 or raw_score > 20:
                        messages.error(request, f'La nota debe estar entre 0 y 20.')
                        continue
                    
                    # Buscar si ya existe
                    grade_record = GradeRecord.objects.filter(
                        enrollment=enrollment,
                        evaluation=selected_evaluation
                    ).first()
                    
                    if grade_record:
                        # Actualizar
                        grade_record.raw_score = raw_score
                        grade_record.save()
                    else:
                        # Crear nuevo
                        GradeRecord.objects.create(
                            enrollment=enrollment,
                            evaluation=selected_evaluation,
                            raw_score=raw_score,
                            recorded_by=request.user
                        )
                except ValueError:
                    messages.error(request, f'Nota inválida para {enrollment.student.get_full_name()}')
        
        messages.success(request, 'Notas registradas exitosamente.')
        return redirect(request.path + f'?evaluation={selected_evaluation_id}')
    
    # Calcular estadísticas si hay evaluación seleccionada
    statistics = None
    if selected_evaluation and enrollments_with_grades:
        grades_list = [item['grade'].rounded_score for item in enrollments_with_grades if item['grade']]
        
        if grades_list:
            statistics = {
                'max': max(grades_list),
                'min': min(grades_list),
                'avg': round(sum(grades_list) / len(grades_list), 2),
                'total': len(grades_list),
            }
    
    context = {
        'course': course,
        'evaluations': evaluations,
        'selected_evaluation': selected_evaluation,
        'enrollments_with_grades': enrollments_with_grades,
        'statistics': statistics,
    }
    
    return render(request, 'professor/record_grades.html', context)


@login_required
def schedule(request):
    """Vista de horario del profesor"""
    
    if request.user.user_role != 'PROFESOR':
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('presentation:login')
    
    # Obtener grupos y labs que enseña
    course_groups = CourseGroup.objects.filter(
        professor=request.user
    ).select_related('course')
    
    lab_groups = LaboratoryGroup.objects.filter(
        professor=request.user
    ).select_related('course')
    
    # Organizar por día
    schedule_by_day = {
        'LUNES': [],
        'MARTES': [],
        'MIERCOLES': [],
        'JUEVES': [],
        'VIERNES': [],
        'SABADO': [],
    }
    
    # Agregar grupos de curso
    for group in course_groups:
        schedule_by_day[group.day_of_week].append({
            'course': group.course.course_name,
            'code': group.course.course_code,
            'type': 'Teoría',
            'group': group.group_code,
            'start_time': group.start_time,
            'end_time': group.end_time,
            'room': group.room,
        })
    
    # Agregar labs
    for lab in lab_groups:
        schedule_by_day[lab.day_of_week].append({
            'course': lab.course.course_name,
            'code': lab.course.course_code,
            'type': f'Lab {lab.lab_nomenclature}',
            'group': lab.lab_nomenclature,
            'start_time': lab.start_time,
            'end_time': lab.end_time,
            'room': lab.room,
        })
    
    # Ordenar por hora
    for day in schedule_by_day:
        schedule_by_day[day].sort(key=lambda x: x['start_time'])
    
    context = {
        'schedule_by_day': schedule_by_day,
    }
    
    return render(request, 'professor/schedule.html', context)