from datetime import time, datetime, timedelta
from collections import defaultdict
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from infrastructure.persistence.models import (
    StudentEnrollment, CourseGroup, LaboratoryGroup,
    GradeRecord, AttendanceRecord, Evaluation, Schedule
)
from collections import defaultdict


@login_required
def dashboard(request):
    """Dashboard principal del alumno"""
    
    # Verificar que sea alumno
    if request.user.user_role != 'ALUMNO':
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('presentation:login')
    
    # Obtener matrículas del alumno
    enrollments = StudentEnrollment.objects.filter(
        student=request.user,
        status='ACTIVO'
    ).select_related('course', 'group', 'lab_assignment__lab_group')
    
    # Calcular estadísticas
    total_courses = enrollments.count()
    avg_attendance = 0
    
    if total_courses > 0:
        total_attendance = sum([e.current_attendance_percentage for e in enrollments])
        avg_attendance = round(total_attendance / total_courses, 2)
    
    context = {
        'enrollments': enrollments,
        'total_courses': total_courses,
        'avg_attendance': avg_attendance,
    }
    
    return render(request, 'student/dashboard.html', context)


@login_required
def schedule(request):
    """Vista de horario del alumno con grid por bloques horarios"""
    
    if request.user.user_role != 'ALUMNO':
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('presentation:login')
    
    # Definir bloques horarios
    time_slots = [
        {'start': '07:00', 'end': '07:50'},
        {'start': '07:50', 'end': '08:40'},
        {'start': '08:50', 'end': '09:40'},
        {'start': '09:40', 'end': '10:30'},
        {'start': '10:40', 'end': '11:30'},
        {'start': '11:30', 'end': '12:20'},
        {'start': '12:20', 'end': '13:10'},
        {'start': '13:10', 'end': '14:00'},
        {'start': '14:00', 'end': '14:50'},
        {'start': '14:50', 'end': '15:40'},
        {'start': '15:50', 'end': '16:40'},
        {'start': '16:40', 'end': '17:30'},
        {'start': '17:40', 'end': '18:30'},
        {'start': '18:30', 'end': '19:20'},
        {'start': '19:20', 'end': '20:10'},
    ]
    
    days = ['LUNES', 'MARTES', 'MIERCOLES', 'JUEVES', 'VIERNES']
    
    # Obtener matrículas del alumno
    enrollments = StudentEnrollment.objects.filter(
        student=request.user,
        status='ACTIVO'
    ).select_related('course', 'group', 'lab_assignment__lab_group__room') # Optimización de consulta
    
    # Crear mapeo de colores por curso
    course_colors = {}
    color_index = 1
    
    for enrollment in enrollments:
        if enrollment.course.course_code not in course_colors:
            course_colors[enrollment.course.course_code] = color_index
            color_index = (color_index % 10) + 1
    
    # Inicializar grid de horarios
    schedule_grid = defaultdict(lambda: defaultdict(list))
    courses_legend = []
    has_collisions = False
    
    # Función auxiliar para convertir time a minutos
    def time_to_minutes(t):
        if isinstance(t, str):
            h, m = map(int, t.split(':'))
            return h * 60 + m
        return t.hour * 60 + t.minute
    
    # Función para encontrar slots ocupados
    def get_occupied_slots(start_time, end_time):
        start_minutes = time_to_minutes(start_time)
        end_minutes = time_to_minutes(end_time)
        occupied = []
        
        for slot in time_slots:
            slot_start = time_to_minutes(slot['start'])
            slot_end = time_to_minutes(slot['end'])
            
            # Verificar si el curso ocupa este slot
            if start_minutes <= slot_start and end_minutes > slot_start:
                occupied.append(slot['start'])
        
        return occupied
    
    # Procesar horarios de teoría
    for enrollment in enrollments:
        if enrollment.group:
            # Obtener los bloques de horario del grupo incluyendo el salón (room)
            schedules = enrollment.group.schedules.select_related('room').all()
            
            for schedule in schedules:
                slots = get_occupied_slots(schedule.start_time, schedule.end_time)
                
                # AQUÍ OCURRE EL CAMBIO PRINCIPAL: Usamos room.name y course.course_name
                room_name = schedule.room.name if schedule.room else 'Sin asignar'
                
                course_info = {
                    'code': enrollment.course.course_code,
                    'name': enrollment.course.course_name,  # Nombre completo del curso
                    'group': enrollment.group.group_code,   # Solo la letra (A, B...)
                    'room': room_name,                      # Nombre completo del salón
                    'type': 'Teoría',
                    'color_index': course_colors[enrollment.course.course_code],
                    'start': schedule.start_time,
                    'end': schedule.end_time
                }
                
                # Agregar a la leyenda
                if not any(c['code'] == course_info['code'] for c in courses_legend):
                    courses_legend.append({
                        'code': course_info['code'],
                        'name': course_info['name'],
                        'color_index': course_info['color_index']
                    })
                
                # Colocar en el grid
                for slot_start in slots:
                    if schedule_grid[schedule.day_of_week][slot_start]:
                        has_collisions = True
                    schedule_grid[schedule.day_of_week][slot_start].append(course_info)
    
    # Procesar horarios de laboratorio
    for enrollment in enrollments:
        if enrollment.lab_assignment:
            lab = enrollment.lab_assignment.lab_group
            slots = get_occupied_slots(lab.start_time, lab.end_time)
            
            room_name = lab.room.name if lab.room else 'Sin asignar'
            
            course_info = {
                'code': enrollment.course.course_code,
                'name': enrollment.course.course_name,
                'group': f"Lab {lab.lab_nomenclature}", # Ej: "Lab A"
                'room': room_name,
                'type': 'Laboratorio',
                'color_index': course_colors[enrollment.course.course_code],
                'start': lab.start_time,
                'end': lab.end_time
            }
            
            for slot_start in slots:
                if schedule_grid[lab.day_of_week][slot_start]:
                    has_collisions = True
                schedule_grid[lab.day_of_week][slot_start].append(course_info)
    
    context = {
        'time_slots': time_slots,
        'days': days,
        'schedule_grid': dict(schedule_grid),
        'courses_legend': courses_legend,
        'has_collisions': has_collisions,
    }
    
    return render(request, 'student/schedule.html', context)


@login_required
def grades(request):
    """Vista de notas del alumno"""
    
    if request.user.user_role != 'ALUMNO':
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('presentation:login')
    
    # Obtener matrículas del alumno
    enrollments = StudentEnrollment.objects.filter(
        student=request.user,
        status='ACTIVO'
    ).select_related('course').prefetch_related('grade_records__evaluation')
    
    # Organizar notas por curso
    courses_data = []
    
    for enrollment in enrollments:
        # Obtener todas las evaluaciones del curso
        evaluations = Evaluation.objects.filter(course=enrollment.course).order_by('unit', 'name')
        
        # Obtener notas del alumno
        grades = GradeRecord.objects.filter(
            enrollment=enrollment
        ).select_related('evaluation')
        
        # Crear diccionario de notas por evaluación
        grades_dict = {grade.evaluation.evaluation_id: grade for grade in grades}
        
        # Organizar por unidad
        units_data = defaultdict(list)
        
        for evaluation in evaluations:
            grade = grades_dict.get(evaluation.evaluation_id)
            units_data[evaluation.unit].append({
                'evaluation': evaluation,
                'grade': grade,
            })
        
        # Calcular promedio por unidad
        unit_averages = {}
        for unit, evals in units_data.items():
            total_percentage = 0
            weighted_sum = 0
            
            for item in evals:
                if item['grade']:
                    weighted_sum += float(item['grade'].rounded_score) * float(item['evaluation'].percentage) / 100
                    total_percentage += float(item['evaluation'].percentage)
            
            if total_percentage > 0:
                unit_averages[unit] = round(weighted_sum, 2)
        
        courses_data.append({
            'enrollment': enrollment,
            'units_data': dict(units_data),
            'unit_averages': unit_averages,
        })
    
    context = {
        'courses_data': courses_data,
    }
    
    return render(request, 'student/grades.html', context)


@login_required
def lab_enrollment(request):
    """Vista de matrícula de laboratorios"""
    
    if request.user.user_role != 'ALUMNO':
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('presentation:login')
    
    # Obtener matrículas sin laboratorio asignado
    enrollments = StudentEnrollment.objects.filter(
        student=request.user,
        status='ACTIVO',
        lab_assignment__isnull=True
    ).select_related('course')
    
    # Obtener laboratorios disponibles para cada curso
    courses_with_labs = []
    
    for enrollment in enrollments:
        labs = LaboratoryGroup.objects.filter(course=enrollment.course).order_by('lab_nomenclature')
        
        if labs.exists():
            courses_with_labs.append({
                'enrollment': enrollment,
                'labs': labs,
            })
    
    # Obtener matrículas con laboratorio asignado
    enrolled_labs = StudentEnrollment.objects.filter(
        student=request.user,
        status='ACTIVO',
        lab_assignment__isnull=False
    ).select_related('course', 'lab_assignment__lab_group')
    
    context = {
        'courses_with_labs': courses_with_labs,
        'enrolled_labs': enrolled_labs,
    }
    
    return render(request, 'student/lab_enrollment.html', context)


@login_required
def syllabus_list(request):
    """Lista de sílabos de los cursos del alumno"""
    
    if request.user.user_role != 'ALUMNO':
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('presentation:login')
    
    # Obtener cursos con sílabo del alumno
    enrollments = StudentEnrollment.objects.filter(
        student=request.user,
        status='ACTIVO',
        course__syllabus__isnull=False  # Solo cursos que tienen sílabo
    ).select_related('course', 'course__syllabus')
    
    # Construir datos con progreso
    courses_with_syllabus = []
    for enrollment in enrollments:
        syllabus = enrollment.course.syllabus
        courses_with_syllabus.append({
            'enrollment': enrollment,
            'course': enrollment.course,
            'syllabus': syllabus,
            'progress': syllabus.get_progress_percentage(),
        })
    
    context = {
        'courses_with_syllabus': courses_with_syllabus,
    }
    
    return render(request, 'student/syllabus_list.html', context)


@login_required
def syllabus_detail(request, course_id):
    """Detalle del sílabo de un curso específico"""
    
    if request.user.user_role != 'ALUMNO':
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('presentation:login')
    
    # Verificar que el alumno esté matriculado en el curso
    try:
        enrollment = StudentEnrollment.objects.select_related(
            'course', 
            'course__syllabus'
        ).get(
            student=request.user,
            course__course_id=course_id,
            status='ACTIVO'
        )
    except StudentEnrollment.DoesNotExist:
        messages.error(request, 'No estás matriculado en este curso.')
        return redirect('presentation:student_syllabus_list')
    
    # Verificar que el curso tenga sílabo
    try:
        syllabus = enrollment.course.syllabus
    except Syllabus.DoesNotExist:
        messages.warning(request, 'Este curso aún no tiene sílabo cargado.')
        return redirect('presentation:student_syllabus_list')
    
    # Obtener sesiones del sílabo
    sessions = syllabus.sessions.all().order_by('session_number')
    
    # Calcular estadísticas
    total_sessions = sessions.count()
    completed_sessions = sessions.filter(real_date__isnull=False).count()
    pending_sessions = total_sessions - completed_sessions
    progress = syllabus.get_progress_percentage()
    
    context = {
        'enrollment': enrollment,
        'course': enrollment.course,
        'syllabus': syllabus,
        'sessions': sessions,
        'total_sessions': total_sessions,
        'completed_sessions': completed_sessions,
        'pending_sessions': pending_sessions,
        'progress': progress,
    }
    
    return render(request, 'student/syllabus_detail.html', context)


@login_required
def attendance_list(request):
    """Lista de asistencia por curso del alumno"""
    
    if request.user.user_role != 'ALUMNO':
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('presentation:login')
    
    # Obtener matrículas del alumno
    enrollments = StudentEnrollment.objects.filter(
        student=request.user,
        status='ACTIVO'
    ).select_related('course')
    
    # Construir datos de asistencia
    attendance_data = []
    for enrollment in enrollments:
        total_records = enrollment.attendance_records.count()
        present_records = enrollment.attendance_records.filter(status__in=['P', 'J']).count()
        absent_records = enrollment.attendance_records.filter(status='F').count()
        
        # Calcular porcentaje
        if total_records > 0:
            percentage = round((present_records / total_records) * 100, 2)
        else:
            percentage = 0
        
        # Determinar estado
        if percentage >= 70:
            status_class = 'success'
            status_text = 'Aprobado'
        elif percentage >= 30:
            status_class = 'warning'
            status_text = 'En Riesgo'
        else:
            status_class = 'danger'
            status_text = 'Crítico'
        
        attendance_data.append({
            'enrollment': enrollment,
            'course': enrollment.course,
            'total_sessions': total_records,
            'present': present_records,
            'absent': absent_records,
            'percentage': percentage,
            'status_class': status_class,
            'status_text': status_text,
        })
    
    context = {
        'attendance_data': attendance_data,
    }
    
    return render(request, 'student/attendance_list.html', context)


@login_required
def attendance_detail(request, course_id):
    """Detalle de asistencia de un curso específico"""
    
    if request.user.user_role != 'ALUMNO':
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('presentation:login')
    
    # Verificar que el alumno esté matriculado en el curso
    try:
        enrollment = StudentEnrollment.objects.select_related('course').get(
            student=request.user,
            course__course_id=course_id,
            status='ACTIVO'
        )
    except StudentEnrollment.DoesNotExist:
        messages.error(request, 'No estás matriculado en este curso.')
        return redirect('presentation:student_attendance_list')
    
    # Obtener registros de asistencia ordenados
    attendance_records = enrollment.attendance_records.all().order_by('session_number')
    
    # Calcular estadísticas
    total_sessions = attendance_records.count()
    present_count = attendance_records.filter(status='P').count()
    justified_count = attendance_records.filter(status='J').count()
    absent_count = attendance_records.filter(status='F').count()
    
    if total_sessions > 0:
        percentage = round(((present_count + justified_count) / total_sessions) * 100, 2)
    else:
        percentage = 0
    
    # Determinar estado
    if percentage >= 70:
        status_class = 'success'
        status_text = 'Aprobado'
    elif percentage >= 30:
        status_class = 'warning'
        status_text = 'En Riesgo'
    else:
        status_class = 'danger'
        status_text = 'Crítico'
    
    context = {
        'enrollment': enrollment,
        'course': enrollment.course,
        'attendance_records': attendance_records,
        'total_sessions': total_sessions,
        'present_count': present_count,
        'justified_count': justified_count,
        'absent_count': absent_count,
        'percentage': percentage,
        'status_class': status_class,
        'status_text': status_text,
    }
    
    return render(request, 'student/attendance_detail.html', context)