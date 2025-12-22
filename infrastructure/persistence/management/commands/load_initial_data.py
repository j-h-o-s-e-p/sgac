import csv
import os
from datetime import date
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from infrastructure.persistence.models import CustomUser, Semester, Course, CourseGroup

class Command(BaseCommand):
    help = 'Carga masiva de cursos, profesores y grupos desde un archivo CSV'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Ruta al archivo CSV de datos')

    def handle(self, *args, **options):
        csv_path = options['csv_file']
        
        self.stdout.write(self.style.MIGRATE_HEADING(f"--- CARGANDO DATOS DESDE: {csv_path} ---"))

        if not os.path.exists(csv_path):
            self.stdout.write(self.style.ERROR(f"Error: El archivo {csv_path} no existe."))
            return

        semester = self.get_or_create_active_semester()
        
        stats = {'courses': 0, 'groups': 0, 'professors': 0, 'errors': []}

        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                with transaction.atomic():
                    for row_num, row in enumerate(reader, start=2):
                        try:
                            if not row.get('Codigo') or not row.get('Asignatura'): continue
                            
                            codigo = row['Codigo'].strip()
                            asignatura = row['Asignatura'].strip()
                            ciclo = row.get('Cicl', 'A').strip()
                            grupo = row.get('Grup', 'A').strip()
                            docente_nombre = row.get('Docentes', '').strip()
                            email = row.get('Correo UNSA', '').strip()
                            
                            # Filtro de ciclo según semestre
                            # if ciclo != semester.name.split('-')[1]: continue
                            
                            # 1. Curso
                            course, created = Course.objects.get_or_create(
                                course_code=codigo,
                                semester=semester,
                                defaults={'course_name': asignatura, 'credits': 3, 'cycle': 1, 'course_type': 'TEORIA'}
                            )
                            if created: 
                                stats['courses'] += 1

                            # 2. Profesor
                            professor = None
                            if docente_nombre and email:
                                professor = self.get_or_create_professor(docente_nombre, email)
                                if professor and professor.date_joined.date() == date.today():
                                    stats['professors'] += 1

                            # 3. Grupo
                            group, g_created = CourseGroup.objects.get_or_create(
                                course=course,
                                group_code=grupo,
                                defaults={'capacity': 50, 'professor': professor}
                            )
                            if g_created:
                                stats['groups'] += 1
                            elif professor and not group.professor:
                                group.professor = professor
                                group.save()

                        except Exception as e:
                            stats['errors'].append(f"Fila {row_num}: {str(e)}")

            # Resumen
            self.stdout.write(self.style.SUCCESS(f"\nPROCESO COMPLETADO"))
            self.stdout.write(f"Cursos creados: {stats['courses']}")
            self.stdout.write(f"Grupos creados: {stats['groups']}")
            self.stdout.write(f"Profesores: {stats['professors']}")
            
            if stats['errors']:
                self.stdout.write(self.style.WARNING(f"\nErrores ({len(stats['errors'])}):"))
                for err in stats['errors'][:5]: self.stdout.write(f"- {err}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error crítico: {str(e)}"))

    def get_or_create_active_semester(self):
        now = date.today()
        period = 'A' if 3 <= now.month <= 7 else 'B'
        
        # Ajuste simple para fechas (puedes refinar esto)
        start = date(now.year, 3, 1) if period == 'A' else date(now.year, 8, 1)
        end = date(now.year, 7, 31) if period == 'A' else date(now.year, 12, 31)
        
        sem, created = Semester.objects.get_or_create(
            name=f"{now.year}-{period}",
            defaults={'start_date': start, 'end_date': end, 'is_active': True}
        )
        if created:
            Semester.objects.exclude(pk=sem.pk).update(is_active=False)
            self.stdout.write(self.style.SUCCESS(f"Semestre {sem.name} creado y activado."))
        return sem

    def get_or_create_professor(self, name, email):
        email = email.strip().lower()
        prof = CustomUser.objects.filter(email=email).first()
        if not prof:
            parts = name.split(',')
            if len(parts) == 2:
                last, first = parts[0].strip().title(), parts[1].strip().title()
            else:
                names = name.strip().title().split()
                first = names[0] if names else 'Docente'
                last = ' '.join(names[1:]) if len(names) > 1 else 'Apellido'
            
            prof = CustomUser.objects.create_user(
                username=email, email=email, first_name=first, last_name=last,
                password='profesor123', user_role='PROFESOR', account_status='ACTIVO'
            )
        return prof