import os
import sys
import django
import csv
from datetime import datetime, date

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()


from infrastructure.persistence.models import (
    CustomUser, Semester, Course, CourseGroup, Classroom
)
from django.db import transaction


def get_or_create_active_semester():
    """Determina y crea el semestre activo según la fecha actual"""
    now = date.today()
    year = now.year
    
    # Determinar periodo A o B
    if 3 <= now.month <= 7:  # Marzo-Julio = Periodo A
        period = 'A'
        start_date = date(year, 3, 1)
        end_date = date(year, 7, 31)
    else:  # Agosto-Diciembre = Periodo B
        period = 'B'
        start_date = date(year, 8, 1)
        end_date = date(year, 12, 31)
    
    semester_name = f"{year}-{period}"
    
    semester, created = Semester.objects.get_or_create(
        name=semester_name,
        defaults={
            'start_date': start_date,
            'end_date': end_date,
            'is_active': True
        }
    )
    
    if created:
        # Desactivar otros semestres
        Semester.objects.exclude(semester_id=semester.semester_id).update(is_active=False)
        print(f"✓ Semestre {semester_name} creado y activado")
    else:
        print(f"✓ Semestre {semester_name} ya existe")
    
    return semester


def get_or_create_professor(name, email):
    """Obtiene o crea un profesor"""
    # Limpiar email
    email = email.strip().lower()
    
    # Buscar por email
    professor = CustomUser.objects.filter(email=email).first()
    
    if not professor:
        # Parsear nombre
        parts = name.split(',')
        if len(parts) == 2:
            last_name = parts[0].strip().title()
            first_name = parts[1].strip().title()
        else:
            names = name.strip().title().split()
            first_name = names[0] if names else 'Profesor'
            last_name = ' '.join(names[1:]) if len(names) > 1 else 'Docente'
        
        # Crear usuario profesor
        professor = CustomUser.objects.create_user(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password='profesor123',  # Contraseña temporal
            user_role='PROFESOR',
            account_status='ACTIVO'
        )
        print(f"  → Profesor creado: {professor.get_full_name()} ({email})")
    
    return professor


def load_courses_from_csv(csv_path):
    """Carga cursos y profesores desde CSV"""
    
    print("\n" + "="*70)
    print("CARGA MASIVA DE CURSOS Y GRUPOS LÓGICOS")
    print("="*70 + "\n")
    
    # Obtener semestre activo
    semester = get_or_create_active_semester()
    
    courses_created = 0
    groups_created = 0
    professors_created = 0
    errors = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            # Leer CSV
            reader = csv.DictReader(file)
            
            with transaction.atomic():
                for row_num, row in enumerate(reader, start=2):
                    try:
                        # Validar datos básicos
                        if not row.get('Codigo') or not row.get('Asignatura'):
                            continue
                        
                        codigo = row['Codigo'].strip()
                        asignatura = row['Asignatura'].strip()
                        ciclo = row.get('Cicl', 'A').strip()
                        grupo = row.get('Grup', 'A').strip()
                        docente = row.get('Docentes', '').strip()
                        email = row.get('Correo UNSA', '').strip()
                        
                        # Solo procesar si coincide con el semestre activo
                        if ciclo != semester.name.split('-')[1]:
                            continue
                        
                        # Obtener o crear curso
                        course, course_created = Course.objects.get_or_create(
                            course_code=codigo,
                            semester=semester,
                            defaults={
                                'course_name': asignatura,
                                'credits': 3,  # Default
                                'cycle': 1,  # Se puede parsear del código si necesario
                                'course_type': 'TEORIA'
                            }
                        )
                        
                        if course_created:
                            courses_created += 1
                            print(f"✓ Curso creado: {codigo} - {asignatura}")
                        
                        # Obtener o crear profesor
                        professor = None
                        if docente and email:
                            professor = get_or_create_professor(docente, email)
                            if professor.date_joined.date() == date.today():
                                professors_created += 1
                        
                        # Obtener o crear grupo lógico
                        group, group_created = CourseGroup.objects.get_or_create(
                            course=course,
                            group_code=grupo,
                            defaults={
                                'capacity': 50,  # Default
                                'professor': professor
                            }
                        )
                        
                        if group_created:
                            groups_created += 1
                            # Imprimimos 'grupo' (el string) no 'group' (el objeto)
                            print(f"  → Grupo Lógico {grupo} creado para {codigo}")
                        elif professor and not group.professor:
                            # Si el grupo ya existía pero no tenía profesor, lo asignamos
                            group.professor = professor
                            group.save()
                            print(f"  → Profesor asignado a grupo {codigo}-{grupo}")
                        
                    except Exception as e:
                        error_msg = f"Error en fila {row_num}: {str(e)}"
                        errors.append(error_msg)
                        print(f"✗ {error_msg}")
        
        # Resumen
        print("\n" + "="*70)
        print("RESUMEN DE CARGA")
        print("="*70)
        print(f"Semestre activo: {semester.name}")
        print(f"Cursos creados: {courses_created}")
        print(f"Grupos Lógicos creados: {groups_created}")
        print(f"Profesores creados: {professors_created}")
        
        if errors:
            print(f"\nErrores encontrados: {len(errors)}")
            for error in errors[:10]: 
                print(f"  - {error}")
        
        print("\n✓ Proceso completado exitosamente\n")
        
    except FileNotFoundError:
        print(f"✗ Error: No se encontró el archivo {csv_path}")
    except Exception as e:
        print(f"✗ Error general: {str(e)}")


if __name__ == '__main__':
    csv_file = 'scripts/data/Curso_Profesor.csv'
    load_courses_from_csv(csv_file)