from collections import defaultdict
from infrastructure.persistence.models import (
    StudentEnrollment, LaboratoryGroup, GradeRecord, Evaluation, Syllabus
)

class StudentService:
    
    @staticmethod
    def get_dashboard_stats(student):
        """Calcula estadísticas para el dashboard principal"""
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
        """Procesa y organiza el horario del estudiante"""
        # Definición de bloques horarios (Constante de negocio)
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

        # Lógica de colores
        course_colors = {}
        color_index = 1
        for enrollment in enrollments:
            if enrollment.course.course_code not in course_colors:
                course_colors[enrollment.course.course_code] = color_index
                color_index = (color_index % 10) + 1

        schedule_grid = defaultdict(lambda: defaultdict(list))
        courses_legend = []
        has_collisions = False

        # Helpers internos
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
                # Verificar si el curso ocupa este slot
                if start_minutes <= slot_start and end_minutes > slot_start:
                    occupied.append(slot['start'])
            return occupied

        # Procesar Teoría
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

                    # Leyenda
                    if not any(c['code'] == course_info['code'] for c in courses_legend):
                        courses_legend.append({
                            'code': course_info['code'],
                            'name': course_info['name'],
                            'color_index': course_info['color_index']
                        })

                    # Grid
                    for slot_start in slots:
                        if schedule_grid[schedule.day_of_week][slot_start]:
                            has_collisions = True
                        schedule_grid[schedule.day_of_week][slot_start].append(course_info)

        # Procesar Laboratorio
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
        """Calcula las notas y promedios por unidad"""
        enrollments = StudentEnrollment.objects.filter(
            student=student, status='ACTIVO'
        ).select_related('course').prefetch_related('grade_records__evaluation')
        
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
        return courses_data

    @staticmethod
    def get_lab_enrollment_options(student):
        """Obtiene laboratorios disponibles y matrículas actuales"""
        # Sin lab asignado
        enrollments_no_lab = StudentEnrollment.objects.filter(
            student=student, status='ACTIVO', lab_assignment__isnull=True
        ).select_related('course')
        
        courses_with_labs = []
        for enrollment in enrollments_no_lab:
            labs = LaboratoryGroup.objects.filter(course=enrollment.course).order_by('lab_nomenclature')
            if labs.exists():
                courses_with_labs.append({'enrollment': enrollment, 'labs': labs})
        
        # Con lab asignado
        enrolled_labs = StudentEnrollment.objects.filter(
            student=student, status='ACTIVO', lab_assignment__isnull=False
        ).select_related('course', 'lab_assignment__lab_group')
        
        return courses_with_labs, enrolled_labs

    @staticmethod
    def get_attendance_summary(student):
        """Calcula porcentajes y estados de asistencia"""
        enrollments = StudentEnrollment.objects.filter(
            student=student, status='ACTIVO'
        ).select_related('course')
        
        attendance_data = []
        for enrollment in enrollments:
            total = enrollment.attendance_records.count()
            present = enrollment.attendance_records.filter(status__in=['P', 'J']).count()
            absent = enrollment.attendance_records.filter(status='F').count()
            
            percentage = round((present / total) * 100, 2) if total > 0 else 0
            
            # Lógica de negocio sobre el estado (esto debería estar aquí, no en la vista)
            if percentage >= 70:
                status_class, status_text = 'success', 'Aprobado'
            elif percentage >= 30:
                status_class, status_text = 'warning', 'En Riesgo'
            else:
                status_class, status_text = 'danger', 'Crítico'
            
            attendance_data.append({
                'enrollment': enrollment,
                'course': enrollment.course,
                'total_sessions': total,
                'present': present,
                'absent': absent,
                'percentage': percentage,
                'status_class': status_class,
                'status_text': status_text,
            })
        return attendance_data