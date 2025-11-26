from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse

# Importar Modelos necesarios para get_object_or_404
from infrastructure.persistence.models import CourseGroup, LaboratoryGroup, Course, Evaluation, GradeRecord, StudentEnrollment, AttendanceRecord, Schedule

# Importar el nuevo servicio
from application.services.professor_services import ProfessorService
from application.services.academic_calendar import get_group_sessions
from datetime import datetime, date, timedelta

# Instanciar servicio
_service = ProfessorService()

# ==================== VISTAS ====================

@login_required
def my_courses(request):
    if request.user.user_role != 'PROFESOR':
        messages.error(request, 'No tienes permisos.')
        return redirect('presentation:login')

    unified_cards = _service.get_professor_courses_cards(request.user)
    return render(request, 'professor/my_courses.html', {'unified_cards': unified_cards})

@login_required
def upload_syllabus(request, course_id):
    if request.user.user_role != 'PROFESOR':
        return redirect('presentation:login')

    if request.method == 'POST' and request.FILES.get('syllabus_pdf'):
        pdf_file = request.FILES['syllabus_pdf']
        if not pdf_file.name.endswith('.pdf'):
            messages.error(request, 'El archivo debe ser formato PDF.')
            return redirect('presentation:professor_my_courses')

        try:
            course = _service.upload_syllabus(course_id, request.user, pdf_file)
            messages.success(request, f'Sílabo de {course.course_code} subido correctamente.')
        except PermissionError:
            messages.error(request, 'No tienes permiso para modificar este curso.')
        except Exception as e:
            messages.error(request, f'Error al subir archivo: {e}')
            
    return redirect('presentation:professor_my_courses')

@login_required
def dashboard(request):
    if request.user.user_role != 'PROFESOR':
        return redirect('presentation:login')
    
    context = _service.get_dashboard_stats(request.user)
    return render(request, 'professor/dashboard.html', context)

@login_required
def attendance(request):
    if request.user.user_role != 'PROFESOR':
        return redirect('presentation:login')
    
    # Reutilizamos la lógica del dashboard para obtener los grupos
    context = _service.get_dashboard_stats(request.user)
    return render(request, 'professor/attendance.html', context)

@login_required
def record_attendance(request, group_id):
    if request.user.user_role != 'PROFESOR':
        return redirect('presentation:login')
    
    # 1. Resolver Grupo (Lógica de vista simple)
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

    # 2. Preparar Datos
    enrollments = _service.get_group_enrollments(group, group_type)
    all_sessions = get_group_sessions(group)
    
    # 3. Determinar Sesión Actual
    selected_date = request.GET.get('date')
    current_session = None
    
    if selected_date:
        try:
            t_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
            current_session = next((s for s in all_sessions if s['date'] == t_date), None)
        except ValueError: pass
    
    if not current_session and all_sessions:
        today_s = next((s for s in all_sessions if s['is_today']), None)
        current_session = today_s if today_s else all_sessions[-1]

    is_editable = current_session['is_today'] if current_session else False

    # 4. Procesar POST (Guardar)
    if request.method == 'POST' and current_session:
        if not is_editable:
            messages.error(request, 'No se puede modificar fechas pasadas.')
        else:
            _service.save_attendance(
                enrollments, 
                current_session['number'], 
                current_session['date'], 
                request.POST, 
                request.user, 
                request.META.get('REMOTE_ADDR')
            )
            messages.success(request, 'Asistencia guardada.')
            return redirect(f"{request.path}?date={current_session['date']}")

    # 5. Mapeo para vista
    attendance_map = {}
    if current_session:
        records = AttendanceRecord.objects.filter(
            enrollment__in=enrollments, session_number=current_session['number']
        )
        attendance_map = {str(r.enrollment_id): r.status for r in records}

    context = {
        'group': group, 'group_type': group_type, 'enrollments': enrollments,
        'all_sessions': all_sessions, 'current_session': current_session,
        'attendance_map': attendance_map, 'is_editable': is_editable
    }
    return render(request, 'professor/record_attendance.html', context)

@login_required
def attendance_report(request, group_id):
    if request.user.user_role != 'PROFESOR': return redirect('presentation:login')
    
    # Resolver grupo 
    try:
        group = CourseGroup.objects.get(group_id=group_id, professor=request.user)
        group_type = 'course'
    except:
        try:
            group = LaboratoryGroup.objects.get(lab_id=group_id, professor=request.user)
            group_type = 'lab'
        except: return redirect('presentation:professor_attendance')

    enrollments = _service.get_group_enrollments(group, group_type)
    sessions = get_group_sessions(group)
    
    # Construir Matriz 
    records = AttendanceRecord.objects.filter(enrollment__in=enrollments)
    records_map = {}
    for r in records:
        if r.enrollment_id not in records_map: records_map[r.enrollment_id] = {}
        records_map[r.enrollment_id][r.session_number] = r.status

    matrix = []
    for env in enrollments:
        s_recs = records_map.get(env.enrollment_id, {})
        row = {'student': env.student, 'enrollment': env, 'attendance_data': []}
        for s in sessions:
            row['attendance_data'].append({'session_number': s['number'], 'status': s_recs.get(s['number'], '-')})
        matrix.append(row)

    if request.GET.get('export') == 'excel':
        wb = _service.generate_attendance_excel(group, sessions, matrix)
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename=Asistencia_{getattr(group, "group_code", "Lab")}.xlsx'
        wb.save(response)
        return response

    return render(request, 'professor/attendance_report.html', {'group': group, 'sessions': sessions, 'matrix': matrix})

@login_required
def grades(request):
    if request.user.user_role != 'PROFESOR': return redirect('presentation:login')
    # Reutilizamos lógica de cursos
    groups = CourseGroup.objects.filter(professor=request.user).select_related('course').distinct()
    courses = set(g.course for g in groups)
    return render(request, 'professor/grades.html', {'courses': courses})

@login_required
def consolidated_grades(request, course_id):
    if request.user.user_role != 'PROFESOR': return redirect('presentation:login')
    
    course = get_object_or_404(Course, course_id=course_id)
    if not CourseGroup.objects.filter(course=course, professor=request.user).exists():
        messages.error(request, 'No enseñas este curso.')
        return redirect('presentation:professor_dashboard')

    # Lógica de estructura de unidades (Presentación)
    evals = Evaluation.objects.filter(course=course).order_by('unit', 'evaluation_type')
    units_structure = {1: [], 2: [], 3: []}
    for e in evals: 
        if e.unit in units_structure: units_structure[e.unit].append(e)

    # Estado de bloqueo
    units_status = {}
    for u, u_evals in units_structure.items():
        count = GradeRecord.objects.filter(evaluation__in=u_evals, enrollment__course=course).count()
        units_status[u] = (count > 0)

    if request.method == 'POST':
        unit = int(request.POST.get('unit_number'))
        if units_status.get(unit):
            messages.error(request, f'Unidad {unit} ya registrada.')
        else:
            saved, errors = _service.save_grades_batch(course, unit, request.POST, request.user)
            if errors: messages.warning(request, f"Guardados {saved}. Errores: {'; '.join(errors[:3])}")
            else: messages.success(request, f'Notas Unidad {unit} guardadas ({saved}).')
            return redirect(request.path)

    # Preparar vista (GET)
    enrollments = StudentEnrollment.objects.filter(course=course, status='ACTIVO').select_related('student').order_by('student__last_name')
    all_grades = GradeRecord.objects.filter(enrollment__in=enrollments, evaluation__course=course)
    grades_map = {g.enrollment_id: {} for g in all_grades}
    for g in all_grades: 
        if g.enrollment_id not in grades_map: grades_map[g.enrollment_id] = {}
        grades_map[g.enrollment_id][g.evaluation_id] = g.rounded_score
    
    matrix_data = []
    for e in enrollments:
        row = {'enrollment': e, 'student': e.student, 'final_grade': e.final_grade, 'grades': {}}
        s_grades = grades_map.get(e.enrollment_id, {})
        for u_evs in units_structure.values():
            for ev in u_evs: row['grades'][ev.evaluation_id] = s_grades.get(ev.evaluation_id)
        matrix_data.append(row)

    return render(request, 'professor/consolidated_grades.html', {
        'course': course, 'units_structure': units_structure,
        'units_status': units_status, 'matrix_data': matrix_data
    })

@login_required
def upload_grades_csv(request, course_id):
    if request.user.user_role != 'PROFESOR': return redirect('presentation:login')
    course = get_object_or_404(Course, course_id=course_id)
    
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        unit = int(request.POST.get('unit_number', 0))
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'El archivo debe ser .csv')
        else:
            try:
                success, errors = _service.process_csv_grades(csv_file, course, unit, request.user)
                if errors: messages.warning(request, f'Cargados {success}. Errores: {"; ".join(errors[:5])}')
                else: messages.success(request, f'Se cargaron {success} notas.')
            except Exception as e:
                messages.error(request, str(e))
                
    return redirect('presentation:professor_record_grades', course_id=course_id)

@login_required
def statistics(request):
    if request.user.user_role != 'PROFESOR': return redirect('presentation:login')
    
    context = _service.get_statistics_context(request.user)
    if not context:
        return render(request, 'professor/statistics.html', {'no_data': True})
        
    return render(request, 'professor/statistics.html', context)

@login_required
def schedule(request):
    """Vista de horario del profesor (Refactorizada)"""
    if request.user.user_role != 'PROFESOR':
        messages.error(request, 'No tienes permisos.')
        return redirect('presentation:login')

    # Delegamos toda la lógica al servicio
    context = _service.get_professor_schedule(request.user)
    
    return render(request, 'professor/schedule.html', context)