from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from infrastructure.persistence.models import (
    StudentEnrollment, CourseGroup, LaboratoryGroup,
    GradeRecord, AttendanceRecord, Evaluation
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
    """Vista de horario del alumno"""
    
    if request.user.user_role != 'ALUMNO':
        messages.error(request, 'No tienes permisos para acceder a esta página.')
        return redirect('presentation:login')
    
    # Obtener matrículas del alumno
    enrollments = StudentEnrollment.objects.filter(
        student=request.user,
        status='ACTIVO'
    ).select_related('course', 'group', 'lab_assignment__lab_group')
    
    # Organizar horarios por día
    schedule_by_day = {
        'LUNES': [],
        'MARTES': [],
        'MIERCOLES': [],
        'JUEVES': [],
        'VIERNES': [],
        'SABADO': [],
    }
    
    for enrollment in enrollments:
        # Horario de teoría
        if enrollment.group:
            schedule_by_day[enrollment.group.day_of_week].append({
                'course': enrollment.course.course_name,
                'code': enrollment.course.course_code,
                'type': 'Teoría',
                'start_time': enrollment.group.start_time,
                'end_time': enrollment.group.end_time,
                'room': enrollment.group.room,
                'professor': enrollment.group.professor.get_full_name() if enrollment.group.professor else 'N/A',
            })
        
        # Horario de laboratorio
        if enrollment.lab_assignment:
            lab = enrollment.lab_assignment.lab_group
            schedule_by_day[lab.day_of_week].append({
                'course': enrollment.course.course_name,
                'code': enrollment.course.course_code,
                'type': f'Lab {lab.lab_nomenclature}',
                'start_time': lab.start_time,
                'end_time': lab.end_time,
                'room': lab.room,
                'professor': lab.professor.get_full_name() if lab.professor else 'N/A',
            })
    
    # Ordenar por hora de inicio
    for day in schedule_by_day:
        schedule_by_day[day].sort(key=lambda x: x['start_time'])
    
    context = {
        'schedule_by_day': schedule_by_day,
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