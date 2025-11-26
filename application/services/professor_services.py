import csv
import openpyxl
from io import TextIOWrapper
from datetime import datetime, date, timedelta
from decimal import Decimal, InvalidOperation
from django.db import transaction
from django.db.models import Avg, Max, Min, Count, Sum, Q
from django.core.files.storage import FileSystemStorage
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

from infrastructure.persistence.models import (
    CourseGroup, LaboratoryGroup, StudentEnrollment,
    AttendanceRecord, GradeRecord, Evaluation, Schedule, 
    Course, CustomUser, Syllabus
)
from application.services.academic_calendar import get_group_sessions

class ProfessorService:
    
    def get_professor_courses_cards(self, user):
        """Prepara la data para las tarjetas de 'Mis Cursos'"""
        course_groups = CourseGroup.objects.filter(professor=user).select_related('course', 'course__syllabus')
        lab_groups = LaboratoryGroup.objects.filter(professor=user).select_related('course', 'course__syllabus')
        
        unified_cards = []
        
        for group in course_groups:
            has_syllabus = hasattr(group.course, 'syllabus') and group.course.syllabus.syllabus_file
            unified_cards.append({
                'type': 'TEORIA',
                'group_obj': group,
                'course': group.course,
                'name': group.course.course_name,
                'code': group.course.course_code,
                'group_label': f"Grupo {group.group_code}",
                'id_for_attendance': group.group_id,
                'id_for_grades': group.course.course_id,
                'has_syllabus': has_syllabus,
                'syllabus_url': group.course.syllabus.syllabus_file.url if has_syllabus else None
            })

        for lab in lab_groups:
            has_syllabus = hasattr(lab.course, 'syllabus') and lab.course.syllabus.syllabus_file
            unified_cards.append({
                'type': 'LABORATORIO',
                'group_obj': lab,
                'course': lab.course,
                'name': lab.course.course_name,
                'code': lab.course.course_code,
                'group_label': f"Lab {lab.lab_nomenclature}",
                'id_for_attendance': lab.lab_id,
                'id_for_grades': None,
                'has_syllabus': has_syllabus,
                'syllabus_url': lab.course.syllabus.syllabus_file.url if has_syllabus else None
            })
            
        return unified_cards

    def upload_syllabus(self, course_id, professor, pdf_file):
        """Lógica para subir sílabo"""
        # Validaciones de negocio
        teoria_exists = CourseGroup.objects.filter(course_id=course_id, professor=professor).exists()
        lab_exists = LaboratoryGroup.objects.filter(course_id=course_id, professor=professor).exists()
        
        if not (teoria_exists or lab_exists):
            raise PermissionError("No tienes permiso para modificar este curso.")
            
        course = Course.objects.get(course_id=course_id)
        Syllabus.objects.update_or_create(
            course=course,
            defaults={'syllabus_file': pdf_file}
        )
        return course

    def get_dashboard_stats(self, professor):
        course_groups = CourseGroup.objects.filter(professor=professor)
        lab_groups = LaboratoryGroup.objects.filter(professor=professor)
        
        total_courses = course_groups.count() + lab_groups.count()
        total_students = course_groups.aggregate(total=Sum('capacity'))['total'] or 0
        
        return {
            'course_groups': course_groups,
            'lab_groups': lab_groups,
            'total_courses': total_courses,
            'total_students': total_students
        }

    def get_group_enrollments(self, group, group_type):
        if group_type == 'course':
            return StudentEnrollment.objects.filter(
                course=group.course, group=group, status='ACTIVO'
            ).select_related('student').order_by('student__last_name', 'student__first_name')
        else:
            return StudentEnrollment.objects.filter(
                lab_assignment__lab_group=group, status='ACTIVO'
            ).select_related('student').order_by('student__last_name', 'student__first_name')

    def save_attendance(self, enrollments, session_number, session_date, post_data, user, ip_address):
        """Guarda la asistencia iterando los enrollments"""
        with transaction.atomic():
            for enrollment in enrollments:
                status = post_data.get(f'status_{enrollment.enrollment_id}')
                if status:
                    AttendanceRecord.objects.update_or_create(
                        enrollment=enrollment,
                        session_number=session_number,
                        defaults={
                            'session_date': session_date,
                            'status': status,
                            'professor_ip': ip_address,
                            'recorded_by': user
                        }
                    )
                    enrollment.calculate_attendance_percentage()

    def generate_attendance_excel(self, group, sessions, matrix):
        """Genera el objeto Workbook (no la respuesta HTTP)"""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Asistencia"
        
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
        
        ws['A1'] = f"Curso: {group.course.course_name}"
        ws['A2'] = f"Grupo: {getattr(group, 'group_code', getattr(group, 'lab_nomenclature', ''))}"
        
        headers = ["Código", "Estudiante", "% Asist"]
        for sess in sessions:
            headers.append(f"S{sess['number']}\n{sess['date'].strftime('%d/%m')}")
            
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col_num, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center', wrap_text=True)
            if col_num > 3:
                ws.column_dimensions[get_column_letter(col_num)].width = 7 

        current_row = 5
        for row_data in matrix:
            ws.cell(row=current_row, column=1, value=row_data['student'].username)
            ws.cell(row=current_row, column=2, value=row_data['student'].get_full_name())
            ws.cell(row=current_row, column=3, value=f"{row_data['enrollment'].current_attendance_percentage}%")
            
            col_idx = 4
            for cell_data in row_data['attendance_data']:
                val = cell_data['status']
                cell = ws.cell(row=current_row, column=col_idx, value=val)
                if val == 'F': cell.font = Font(color="FF0000", bold=True)
                elif val == 'P': cell.font = Font(color="008000")
                elif val == 'J': cell.font = Font(color="FFA500")
                col_idx += 1
            current_row += 1
            
        ws.column_dimensions['B'].width = 30
        return wb

    def save_grades_batch(self, course, unit_to_save, post_data, user):
        """Guarda notas masivamente desde el formulario web"""
        all_evaluations = Evaluation.objects.filter(course=course, unit=unit_to_save)
        enrollments = StudentEnrollment.objects.filter(course=course, status='ACTIVO')
        
        count_saved = 0
        errors = []
        
        with transaction.atomic():
            for enrollment in enrollments:
                for evaluation in all_evaluations:
                    input_name = f"grade_{enrollment.enrollment_id}_{evaluation.evaluation_id}"
                    raw_score = post_data.get(input_name)

                    if raw_score and raw_score.strip():
                        try:
                            val = Decimal(raw_score)
                            if not (0 <= val <= 20):
                                errors.append(f"Nota inválida para {enrollment.student.get_full_name()}")
                                continue
                            
                            GradeRecord.objects.update_or_create(
                                enrollment=enrollment,
                                evaluation=evaluation,
                                defaults={'raw_score': val, 'recorded_by': user}
                            )
                            count_saved += 1
                        except (ValueError, InvalidOperation):
                            errors.append(f"Formato inválido para {enrollment.student.get_full_name()}")
                
                enrollment.calculate_final_grade()
        
        return count_saved, errors

    def process_csv_grades(self, csv_file, course, unit_number, user):
        """Procesa el archivo CSV y guarda las notas"""
        file_data = TextIOWrapper(csv_file.file, encoding='utf-8')
        csv_reader = csv.DictReader(file_data)
        
        evaluations = Evaluation.objects.filter(course=course, unit=unit_number)
        eval_continua = evaluations.filter(evaluation_type='CONTINUA').first()
        eval_examen = evaluations.filter(evaluation_type='EXAMEN').first()
        
        if not eval_continua or not eval_examen:
            raise ValueError("Faltan evaluaciones configuradas para esta unidad")

        field_names = csv_reader.fieldnames
        col_continua = f'continua{unit_number}' if f'continua{unit_number}' in field_names else 'continua1'
        col_examen = f'examen{unit_number}' if f'examen{unit_number}' in field_names else 'examen1'

        success_count = 0
        errors = []

        with transaction.atomic():
            for row in csv_reader:
                cui = row.get('cui', '').strip()
                if not cui: continue
                
                try:
                    student = CustomUser.objects.get(username=cui, user_role='ALUMNO')
                    enrollment = StudentEnrollment.objects.get(student=student, course=course, status='ACTIVO')
                    
                    for col, eval_obj in [(col_continua, eval_continua), (col_examen, eval_examen)]:
                        score_str = row.get(col, '').strip()
                        if score_str:
                            val = Decimal(score_str)
                            if 0 <= val <= 20:
                                GradeRecord.objects.update_or_create(
                                    enrollment=enrollment,
                                    evaluation=eval_obj,
                                    defaults={'raw_score': val, 'recorded_by': user}
                                )
                                success_count += 1
                    
                    enrollment.calculate_final_grade()
                except Exception as e:
                    errors.append(f"Error en {cui}: {str(e)}")
                    
        return success_count, errors

    def get_statistics_context(self, professor):
        groups = CourseGroup.objects.filter(professor=professor).select_related('course')
        if not groups.exists():
            return None

        all_enrollments = StudentEnrollment.objects.filter(group__in=groups, status='ACTIVO')
        
        global_stats = all_enrollments.aggregate(
            promedio_general=Avg('final_grade'),
            asistencia_promedio=Avg('current_attendance_percentage'),
            total_alumnos=Count('enrollment_id')
        )
        
        aprobados = all_enrollments.filter(final_grade__gte=10.5).count()
        desaprobados = all_enrollments.filter(final_grade__lt=10.5).count()
        habilitados = all_enrollments.filter(current_attendance_percentage__gte=70).count()

        course_performance = []
        chart_labels = []
        chart_grades = []
        chart_attendance = []

        for group in groups:
            qs = group.enrollments.filter(status='ACTIVO')
            stats = qs.aggregate(avg=Avg('final_grade'), max=Max('final_grade'), min=Min('final_grade'), att=Avg('current_attendance_percentage'))
            
            avg_grade = stats['avg'] or 0
            avg_att = stats['att'] or 0
            
            course_performance.append({
                'course_name': group.course.course_name,
                'group_code': group.group_code,
                'avg_grade': round(avg_grade, 2),
                'max_grade': stats['max'] or 0,
                'min_grade': stats['min'] or 0,
                'avg_attendance': round(avg_att, 1),
                'student_count': qs.count()
            })
            
            chart_labels.append(f"{group.course.course_code} - {group.group_code}")
            chart_grades.append(float(round(avg_grade, 2)))
            chart_attendance.append(float(round(avg_att, 1)))

        at_risk = all_enrollments.filter(
            Q(final_grade__lt=10.5) | Q(current_attendance_percentage__lt=70)
        ).select_related('student', 'course').order_by('final_grade')[:10]

        return {
            'no_data': False,
            'global_stats': global_stats,
            'aprobados_count': aprobados,
            'desaprobados_count': desaprobados,
            'habilitados_count': habilitados,
            'course_performance': course_performance,
            'at_risk_students': at_risk,
            'chart_labels': chart_labels,
            'chart_grades': chart_grades,
            'chart_attendance': chart_attendance,
        }

    def get_professor_schedule(self, professor):
        """Procesa y organiza el horario semanal del profesor"""
        
        # Estructura base
        schedule_by_day = {
            'LUNES': [],
            'MARTES': [],
            'MIERCOLES': [],
            'JUEVES': [],
            'VIERNES': [],
            'SABADO': [],
        }

        total_duration = timedelta()
        total_classes = 0
        unique_course_codes = set()
        
        # 1. Obtener los horarios de Cursos (Teoría)
        course_schedules = Schedule.objects.filter(
            course_group__professor=professor
        ).select_related(
            'course_group',        
            'course_group__course', 
            'room'                  
        )

        # 2. Obtener los horarios de Laboratorio (Si tuvieras implementado esto en el futuro)
        # lab_schedules = ... (lógica similar)

        # 3. Procesar los horarios
        for entry in course_schedules:
            # Calcular duración para estadísticas
            time_start = datetime.combine(date.min, entry.start_time)
            time_end = datetime.combine(date.min, entry.end_time)
            duration = time_end - time_start
            
            total_duration += duration
            total_classes += 1
            unique_course_codes.add(entry.course_group.course.course_code)

            # Agregar al día correspondiente
            if entry.day_of_week in schedule_by_day:
                schedule_by_day[entry.day_of_week].append({
                    'course': entry.course_group.course.course_name,
                    'code': entry.course_group.course.course_code,
                    'type': 'Teoría',
                    'group': entry.course_group.group_code,
                    'start_time': entry.start_time,
                    'end_time': entry.end_time,
                    'room': entry.room, 
                })
        
        # 4. Ordenar cada día por hora de inicio
        for day in schedule_by_day:
            schedule_by_day[day].sort(key=lambda x: x['start_time'])
        
        total_hours_decimal = total_duration.total_seconds() / 3600

        return {
            'schedule_by_day': schedule_by_day,
            'total_horas': round(total_hours_decimal, 1),
            'total_clases': total_classes,
            'total_cursos': len(unique_course_codes),
        }