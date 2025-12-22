from collections import defaultdict
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from infrastructure.persistence.models import (
    StudentEnrollment, LaboratoryGroup, GradeRecord, Evaluation, Schedule,
    Syllabus, SessionProgress, LabEnrollmentCampaign, StudentPostulation
)

class StudentService:
    
    @staticmethod
    def get_dashboard_stats(student):
        """Saco los totales de cursos y promedios para el home"""
        enrollments = StudentEnrollment.objects.filter(
            student=student,
            status='ACTIVO'
        ).select_related('course', 'group', 'lab_assignment__lab_group')
        
        total_courses = enrollments.count()
        avg_attendance = 0
        
        if total_courses > 0:
            total_attendance = sum([e.current_attendance_percentage for e in enrollments])
            avg_attendance = round(total_attendance / total_courses, 2)
            
        return {
            'enrollments': enrollments,
            'total_courses': total_courses,
            'avg_attendance': avg_attendance
        }

    @staticmethod
    def get_student_schedule(student):
        """Armo el horario cruzando datos de teoría y laboratorio"""
        # Bloques horarios definidos
        TIME_SLOTS = [
            {'start': '07:00', 'end': '07:50'}, {'start': '07:50', 'end': '08:40'},
            {'start': '08:50', 'end': '09:40'}, {'start': '09:40', 'end': '10:30'},
            {'start': '10:40', 'end': '11:30'}, {'start': '11:30', 'end': '12:20'},
            {'start': '12:20', 'end': '13:10'}, {'start': '13:10', 'end': '14:00'},
            {'start': '14:00', 'end': '14:50'}, {'start': '14:50', 'end': '15:40'},
            {'start': '15:50', 'end': '16:40'}, {'start': '16:40', 'end': '17:30'},
            {'start': '17:40', 'end': '18:30'}, {'start': '18:30', 'end': '19:20'},
            {'start': '19:20', 'end': '20:10'},
        ]
        DAYS = ['LUNES', 'MARTES', 'MIERCOLES', 'JUEVES', 'VIERNES']

        enrollments = StudentEnrollment.objects.filter(
            student=student, status='ACTIVO'
        ).select_related('course', 'group', 'lab_assignment__lab_group__room')

        # Asigno colores a los cursos para que se vea bonito
        course_colors = {}
        color_index = 1
        for enrollment in enrollments:
            if enrollment.course.course_code not in course_colors:
                course_colors[enrollment.course.course_code] = color_index
                color_index = (color_index % 10) + 1

        schedule_grid = defaultdict(lambda: defaultdict(list))
        courses_legend = []
        has_collisions = False

        # Helpers para calcular minutos y choques
        def time_to_minutes(t):
            if isinstance(t, str):
                h, m = map(int, t.split(':'))
                return h * 60 + m
            return t.hour * 60 + t.minute

        def get_occupied_slots(start_time, end_time):
            start_minutes = time_to_minutes(start_time)
            end_minutes = time_to_minutes(end_time)
            occupied = []
            for slot in TIME_SLOTS:
                slot_start = time_to_minutes(slot['start'])
                if start_minutes <= slot_start and end_minutes > slot_start:
                    occupied.append(slot['start'])
            return occupied

        # 1. Proceso horarios de Teoría
        for enrollment in enrollments:
            if enrollment.group:
                schedules = enrollment.group.schedules.select_related('room').all()
                for schedule in schedules:
                    slots = get_occupied_slots(schedule.start_time, schedule.end_time)
                    room_name = schedule.room.name if schedule.room else 'Sin asignar'
                    
                    course_info = {
                        'code': enrollment.course.course_code,
                        'name': enrollment.course.course_name,
                        'group': enrollment.group.group_code,
                        'room': room_name,
                        'type': 'Teoría',
                        'color_index': course_colors[enrollment.course.course_code],
                        'start': schedule.start_time,
                        'end': schedule.end_time
                    }

                    if not any(c['code'] == course_info['code'] for c in courses_legend):
                        courses_legend.append({
                            'code': course_info['code'],
                            'name': course_info['name'],
                            'color_index': course_info['color_index']
                        })

                    for slot_start in slots:
                        if schedule_grid[schedule.day_of_week][slot_start]:
                            has_collisions = True
                        schedule_grid[schedule.day_of_week][slot_start].append(course_info)

        # 2. Proceso horarios de Laboratorio
        for enrollment in enrollments:
            if enrollment.lab_assignment:
                lab = enrollment.lab_assignment.lab_group
                slots = get_occupied_slots(lab.start_time, lab.end_time)
                room_name = lab.room.name if lab.room else 'Sin asignar'
                
                course_info = {
                    'code': enrollment.course.course_code,
                    'name': enrollment.course.course_name,
                    'group': f"Lab {lab.lab_nomenclature}",
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

        return {
            'time_slots': TIME_SLOTS,
            'days': DAYS,
            'schedule_grid': dict(schedule_grid),
            'courses_legend': courses_legend,
            'has_collisions': has_collisions
        }

    @staticmethod
    def get_grades_summary(student):
        """Calculo promedios por unidad y nota final"""
        enrollments = StudentEnrollment.objects.filter(
            student=student, status='ACTIVO'
        ).select_related('course','group').prefetch_related('grade_records__evaluation')
        
        courses_data = []
        for enrollment in enrollments:
            evaluations = Evaluation.objects.filter(course=enrollment.course).order_by('unit', 'name')
            grades = GradeRecord.objects.filter(enrollment=enrollment).select_related('evaluation')
            grades_dict = {grade.evaluation.evaluation_id: grade for grade in grades}
            
            units_data = defaultdict(list)
            for evaluation in evaluations:
                grade = grades_dict.get(evaluation.evaluation_id)
                units_data[evaluation.unit].append({
                    'evaluation': evaluation,
                    'grade': grade,
                })
            
            # Calculo ponderado por unidad
            unit_averages = {}
            for unit, evals in units_data.items():
                total_percentage = 0
                weighted_sum = 0
                for item in evals:
                    if item['grade']:
                        # Nota: el modelo GradeRecord ya tiene rounded_score
                        weighted_sum += float(item['grade'].rounded_score) * float(item['evaluation'].percentage) / 100
                        total_percentage += float(item['evaluation'].percentage)
                
                if total_percentage > 0:
                    unit_averages[unit] = round(weighted_sum, 2)
            
            courses_data.append({
                'enrollment': enrollment,
                'units_data': dict(units_data),
                'unit_averages': unit_averages,
            })
        return courses_data

    @staticmethod
    def get_lab_enrollment_options(student):
        """Veo qué laboratorios puede elegir el alumno"""
        # Cursos donde le falta matricularse a lab
        enrollments_no_lab = StudentEnrollment.objects.filter(
            student=student, status='ACTIVO', lab_assignment__isnull=True
        ).select_related('course')
        
        courses_with_labs = []
        for enrollment in enrollments_no_lab:
            labs = LaboratoryGroup.objects.filter(course=enrollment.course).order_by('lab_nomenclature')
            if labs.exists():
                courses_with_labs.append({'enrollment': enrollment, 'labs': labs})
        
        # Labs donde ya tiene cupo
        enrolled_labs = StudentEnrollment.objects.filter(
            student=student, status='ACTIVO', lab_assignment__isnull=False
        ).select_related('course', 'lab_assignment__lab_group')
        
        return courses_with_labs, enrolled_labs

    @staticmethod
    def get_attendance_summary(student):
        """Resumen general de asistencia de todos los cursos"""
        enrollments = StudentEnrollment.objects.filter(
            student=student, status='ACTIVO'
        ).select_related('course', 'group')
        
        attendance_data = []
        for enrollment in enrollments:
            data = StudentService._calculate_attendance_metrics(enrollment)
            attendance_data.append(data)
        return attendance_data

    @staticmethod
    def get_syllabus_list(student):
        """Lista los cursos que tienen sílabo cargado"""
        enrollments = StudentEnrollment.objects.filter(
            student=student,
            status='ACTIVO',
            course__syllabus__isnull=False
        ).select_related('course', 'course__syllabus', 'group')
        
        data = []
        for enrollment in enrollments:
            syllabus = enrollment.course.syllabus
            data.append({
                'enrollment': enrollment,
                'course': enrollment.course,
                'syllabus': syllabus,
                'progress': syllabus.get_progress_percentage(),
            })
        return data

    @staticmethod
    def get_syllabus_detail(student, course_id):
        """
        Detalle completo del avance del sílabo.
        Retorna un dict con datos o None si hay error.
        """
        try:
            enrollment = StudentEnrollment.objects.select_related(
                'course', 'course__syllabus', 'group'
            ).get(student=student, course__course_id=course_id, status='ACTIVO')
        except ObjectDoesNotExist:
            return {'error': 'not_enrolled'}
        
        if not hasattr(enrollment.course, 'syllabus'):
            return {'error': 'no_syllabus'}
            
        syllabus = enrollment.course.syllabus
        sessions = syllabus.sessions.all().select_related('progress').order_by('session_number')
        
        total_sessions = sessions.count()
        
        # Cuento las sesiones marcadas como completadas para ESTE grupo
        completed_sessions = SessionProgress.objects.filter(
            session__syllabus=syllabus,
            course_group=enrollment.group
        ).count()
        
        return {
            'success': True,
            'enrollment': enrollment,
            'course': enrollment.course,
            'syllabus': syllabus,
            'sessions': sessions,
            'total_sessions': total_sessions,
            'completed_sessions': completed_sessions,
            'pending_sessions': total_sessions - completed_sessions,
            'progress': syllabus.get_progress_percentage(),
        }

    @staticmethod
    def get_attendance_detail(student, course_id):
        """Detalle de faltas y asistencias de un solo curso"""
        try:
            enrollment = StudentEnrollment.objects.select_related('course', 'group').get(
                student=student, course__course_id=course_id, status='ACTIVO'
            )
        except ObjectDoesNotExist:
            return None # O lanzar excepción controlada
            
        # Reutilizo la lógica de cálculo
        return StudentService._calculate_attendance_metrics(enrollment, include_records=True)

    @staticmethod
    def _calculate_attendance_metrics(enrollment, include_records=False):
        """Helper privado para no repetir la lógica del 70% / 30%"""
        # Si me piden el detalle, traigo los objetos, sino solo cuento
        records_qs = enrollment.attendance_records.all().order_by('session_number')
        
        total = records_qs.count()
        present = records_qs.filter(status='P').count()
        justified = records_qs.filter(status='J').count() # La 'J' cuenta como asistencia para el %
        absent = records_qs.filter(status='F').count()
        
        percentage = round(((present + justified) / total) * 100, 2) if total > 0 else 0
        
        # Regla de negocio visual
        if percentage >= 70:
            status_class, status_text = 'success', 'Aprobado'
        elif percentage >= 30:
            status_class, status_text = 'warning', 'En Riesgo'
        else:
            status_class, status_text = 'danger', 'Crítico'
            
        result = {
            'enrollment': enrollment,
            'course': enrollment.course,
            'total_sessions': total,
            'present_count': present,
            'justified_count': justified,
            'absent_count': absent,
            'percentage': percentage,
            'status_class': status_class,
            'status_text': status_text,
        }
        
        if include_records:
            result['attendance_records'] = records_qs
            
        return result

    # ==================== INSCRIPCIÓN DE LABORATORIOS ====================
    
    @staticmethod
    def get_available_lab_campaigns(student):
        """
        Obtiene las campañas activas donde el alumno puede inscribirse
        Retorna: Lista de cursos con labs disponibles y sus campañas
        """
        # 1. Cursos activos del estudiante SIN lab asignado
        enrollments_no_lab = StudentEnrollment.objects.filter(
            student=student,
            status='ACTIVO',
            lab_assignment__isnull=True
        ).select_related('course')
        
        campaigns_data = []
        
        for enrollment in enrollments_no_lab:
            # 2. Verificar si hay campaña activa para este curso
            campaign = LabEnrollmentCampaign.objects.filter(
                course=enrollment.course,
                is_closed=False
            ).first()
            
            if not campaign:
                continue 
            
            # 3. Verificar si ya postuló
            already_postulated = StudentPostulation.objects.filter(
                campaign=campaign,
                student=student
            ).first()
            
            # 4. Obtener todos los labs del curso
            labs = LaboratoryGroup.objects.filter(
                course=enrollment.course
            ).select_related('room', 'professor', 'external_professor')
            
            # 5. Por cada lab, verificar conflictos de horario
            labs_with_status = []
            for lab in labs:
                has_conflict = StudentService._check_student_lab_conflict(student, lab)
                
                # Contar cuántos ya están inscritos
                enrolled_count = StudentPostulation.objects.filter(
                    campaign=campaign,
                    lab_group=lab
                ).count()
                
                labs_with_status.append({
                    'lab': lab,
                    'has_conflict': has_conflict,
                    'enrolled_count': enrolled_count,
                    'is_full': enrolled_count >= lab.capacity,
                    'available_spots': max(0, lab.capacity - enrolled_count)
                })
            
            campaigns_data.append({
                'enrollment': enrollment,
                'campaign': campaign,
                'labs': labs_with_status,
                'already_postulated': already_postulated,
                'can_postulate': not already_postulated
            })
        
        return campaigns_data
    
    @staticmethod
    def get_enrolled_labs(student):
        """
        Labs donde el alumno YA tiene asignación (confirmada)
        """
        return StudentEnrollment.objects.filter(
            student=student,
            status='ACTIVO',
            lab_assignment__isnull=False
        ).select_related(
            'course',
            'lab_assignment__lab_group__room',
            'lab_assignment__lab_group__professor',
            'lab_assignment__lab_group__external_professor'
        )
    
    @staticmethod
    def _check_student_lab_conflict(student, lab_group):
        """
        Verifica si el alumno tiene cruce de horario con este lab
        Revisa: 
        - Horarios de teoría de TODOS sus cursos
        - Otros labs ya asignados
        - Otras postulaciones pendientes en otras campañas
        """
        def overlap(s1, e1, s2, e2):
            return s1 < e2 and s2 < e1
        
        # 1. Obtener todas las matrículas activas del alumno
        enrollments = StudentEnrollment.objects.filter(
            student=student,
            status='ACTIVO'
        ).select_related('course', 'group')
        
        for enrollment in enrollments:
            # 2. Verificar horarios de teoría
            if enrollment.group:
                schedules = Schedule.objects.filter(course_group=enrollment.group)
                for sch in schedules:
                    if sch.day_of_week == lab_group.day_of_week:
                        if overlap(
                            lab_group.start_time, lab_group.end_time,
                            sch.start_time, sch.end_time
                        ):
                            return True
            
            # 3. Verificar labs ya asignados
            if enrollment.lab_assignment:
                other_lab = enrollment.lab_assignment.lab_group
                if other_lab.lab_id != lab_group.lab_id:
                    if other_lab.day_of_week == lab_group.day_of_week:
                        if overlap(
                            lab_group.start_time, lab_group.end_time,
                            other_lab.start_time, other_lab.end_time
                        ):
                            return True
        
        # 4. Verificar otras postulaciones pendientes (en otras campañas activas)
        other_postulations = StudentPostulation.objects.filter(
            student=student,
            status='PENDIENTE'
        ).select_related('lab_group')
        
        for post in other_postulations:
            if post.lab_group.lab_id != lab_group.lab_id:
                if post.lab_group.day_of_week == lab_group.day_of_week:
                    if overlap(
                        lab_group.start_time, lab_group.end_time,
                        post.lab_group.start_time, post.lab_group.end_time
                    ):
                        return True
        
        return False
    
    @staticmethod
    @transaction.atomic
    def postulate_to_lab(student, campaign_id, lab_id):
        """
        El alumno postula a un laboratorio específico
        """
        result = {'success': False, 'errors': []}
        
        try:
            # 1. Validar que la campaña existe y está activa
            campaign = LabEnrollmentCampaign.objects.filter(
                campaign_id=campaign_id,
                is_closed=False
            ).first()
            
            if not campaign:
                result['errors'].append('La campaña de inscripción no está disponible.')
                return result
            
            # 2. Verificar que el alumno está matriculado en el curso
            enrollment = StudentEnrollment.objects.filter(
                student=student,
                course=campaign.course,
                status='ACTIVO'
            ).first()
            
            if not enrollment:
                result['errors'].append('No estás matriculado en este curso.')
                return result
            
            # 3. Verificar que el lab existe
            lab = LaboratoryGroup.objects.filter(
                lab_id=lab_id,
                course=campaign.course
            ).first()
            
            if not lab:
                result['errors'].append('El laboratorio seleccionado no existe.')
                return result
            
            # 4. Verificar que no tenga postulación previa en esta campaña
            existing = StudentPostulation.objects.filter(
                campaign=campaign,
                student=student
            ).first()
            
            if existing:
                result['errors'].append('Ya postulaste a un laboratorio en esta campaña.')
                return result
            
            # 5. Verificar conflictos de horario
            if StudentService._check_student_lab_conflict(student, lab):
                result['errors'].append('Tienes un cruce de horario con este laboratorio.')
                return result
            
            # 6. Crear postulación
            postulation = StudentPostulation.objects.create(
                campaign=campaign,
                student=student,
                lab_group=lab,
                status='PENDIENTE'
            )
            
            result['success'] = True
            result['postulation_id'] = str(postulation.postulation_id)
            
        except Exception as e:
            result['errors'].append(f'Error al procesar inscripción: {str(e)}')
        
        return result
    
    @staticmethod
    def get_student_postulations(student):
        """
        Obtiene todas las postulaciones del alumno (pendientes y procesadas)
        """
        postulations = StudentPostulation.objects.filter(
            student=student
        ).select_related(
            'campaign__course',
            'lab_group__room',
            'lab_group__professor',
            'lab_group__external_professor'
        ).order_by('-timestamp')
        
        data = []
        for post in postulations:
            status_info = {
                'PENDIENTE': {'class': 'warning', 'text': 'En espera', 'icon': 'hourglass-split'},
                'ACEPTADO': {'class': 'success', 'text': 'Asignado', 'icon': 'check-circle'},
                'REASIGNADO': {'class': 'info', 'text': 'Reasignado', 'icon': 'arrow-repeat'},
                'RECHAZADO': {'class': 'danger', 'text': 'No asignado', 'icon': 'x-circle'}
            }.get(post.status, {'class': 'secondary', 'text': post.status, 'icon': 'question-circle'})
            
            data.append({
                'postulation': post,
                'status_info': status_info
            })
        
        return data

    @staticmethod
    def get_lab_details_dto(lab_id, student):
        """
        Obtiene los detalles de un laboratorio formateados para consumo JSON (DTO).
        Incluye validación de conflictos horarios para el estudiante.
        """
        try:
            from infrastructure.persistence.models import LaboratoryGroup
            
            # 1. Obtener datos crudos
            lab = LaboratoryGroup.objects.select_related(
                'room', 'professor', 'external_professor', 'course'
            ).get(lab_id=lab_id)
            
            # 2. Verificar conflicto (Usando lógica interna del servicio)
            # Nota: Asumo que _check_student_lab_conflict es un método de esta misma clase
            has_conflict = StudentService._check_student_lab_conflict(student, lab)
            
            # 3. Formatear nombre del profesor
            professor_name = 'Sin asignar'
            if lab.professor:
                professor_name = lab.professor.get_full_name()
            elif lab.external_professor:
                professor_name = lab.external_professor.full_name
            
            # 4. Construir DTO de respuesta
            return {
                'success': True,
                'lab': {
                    'id': str(lab.lab_id),
                    'nomenclature': lab.lab_nomenclature,
                    'capacity': lab.capacity,
                    'day': lab.get_day_of_week_display(),
                    'start_time': lab.start_time.strftime('%H:%M'),
                    'end_time': lab.end_time.strftime('%H:%M'),
                    'room': lab.room.name if lab.room else 'Sin asignar',
                    'professor': professor_name,
                    'has_conflict': has_conflict
                }
            }
            
        except LaboratoryGroup.DoesNotExist:
            return {
                'success': False,
                'error': 'Laboratorio no encontrado'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Error al obtener detalles: {str(e)}"
            }