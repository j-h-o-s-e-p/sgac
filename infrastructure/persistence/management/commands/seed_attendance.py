import random
from datetime import date
from django.core.management.base import BaseCommand
from django.db import transaction
from infrastructure.persistence.models import (
    CourseGroup, LaboratoryGroup, StudentEnrollment, 
    AttendanceRecord, CustomUser
)
from application.services.academic_calendar import get_group_sessions, get_lab_sessions

class Command(BaseCommand):
    help = 'Puebla aleatoriamente la asistencia para un curso específico (Testing)'

    def add_arguments(self, parser):
        parser.add_argument('--course', type=str, default='1703237', help='Código del curso (Default: IS2)')

    def handle(self, *args, **options):
        codigo_curso = options['course']
        opciones = ['P', 'F', 'J']
        pesos = [0.80, 0.15, 0.05]
        hoy = date.today()
        total = 0
        
        # Usuario fallback si el grupo no tiene profesor asignado
        fallback_user = CustomUser.objects.filter(is_superuser=True).first()

        self.stdout.write(f"--- POBLANDO ASISTENCIA PARA: {codigo_curso} ---")

        # 1. TEORÍA
        grupos = CourseGroup.objects.filter(course__course_code=codigo_curso)
        for grupo in grupos:
            self.stdout.write(f" -> Procesando Grupo: {grupo.group_code}")
            try:
                sesiones = get_group_sessions(grupo)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"   Error calendario: {e}"))
                continue

            enrollments = StudentEnrollment.objects.filter(group=grupo, status='ACTIVO')
            prof = grupo.professor if grupo.professor else fallback_user

            with transaction.atomic():
                for sesion in sesiones:
                    if sesion['date'] <= hoy:
                        for env in enrollments:
                            if not AttendanceRecord.objects.filter(enrollment=env, session_number=sesion['number']).exists():
                                AttendanceRecord.objects.create(
                                    enrollment=env,
                                    session_number=sesion['number'],
                                    session_date=sesion['date'],
                                    status=random.choices(opciones, weights=pesos, k=1)[0],
                                    professor_ip='127.0.0.1',
                                    recorded_by=prof
                                )
                                env.calculate_attendance_percentage()
                                total += 1

        # 2. LABORATORIOS
        labs = LaboratoryGroup.objects.filter(course__course_code=codigo_curso)
        for lab in labs:
            self.stdout.write(f" -> Procesando Laboratorio: {lab.lab_nomenclature}")
            try:
                sesiones = get_lab_sessions(lab)
            except: continue

            enrollments = StudentEnrollment.objects.filter(lab_assignment__lab_group=lab, status='ACTIVO')
            prof = lab.professor if lab.professor else fallback_user

            with transaction.atomic():
                for sesion in sesiones:
                    if sesion['date'] <= hoy:
                        for env in enrollments:
                            if not AttendanceRecord.objects.filter(enrollment=env, session_number=sesion['number']).exists():
                                AttendanceRecord.objects.create(
                                    enrollment=env,
                                    session_number=sesion['number'],
                                    session_date=sesion['date'],
                                    status=random.choices(opciones, weights=pesos, k=1)[0],
                                    professor_ip='127.0.0.1',
                                    recorded_by=prof
                                )
                                env.calculate_attendance_percentage()
                                total += 1

        self.stdout.write(self.style.SUCCESS(f"✅ LISTO: {total} registros creados para el curso {codigo_curso}."))