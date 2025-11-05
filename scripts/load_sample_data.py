"""
Script para cargar datos de prueba en el sistema
Ejecutar: python manage.py shell < scripts/load_sample_data.py
"""

from infrastructure.persistence.models import (
    CustomUser, Semester, Course, CourseGroup, LaboratoryGroup,
    Evaluation, StudentEnrollment, GradeRecord, AttendanceRecord
)
from datetime import date, time, datetime, timedelta
from decimal import Decimal

print("=" * 50)
print(" CARGANDO DATOS DE PRUEBA")
print("=" * 50)

# 1. CREAR SEMESTRE
print("\n Creando semestre...")
semester, created = Semester.objects.get_or_create(
    name="2024-2",
    defaults={
        'start_date': date(2024, 8, 1),
        'end_date': date(2024, 12, 20),
        'is_active': True
    }
)
print(f"✅ Semestre: {semester.name}")

# 2. CREAR USUARIOS
print("\n Creando usuarios...")

# Profesor 1
profesor1, created = CustomUser.objects.get_or_create(
    email="profesor1@universidad.edu.pe",
    defaults={
        'username': 'profesor1@universidad.edu.pe',
        'first_name': 'Carlos',
        'last_name': 'Ramírez',
        'user_role': 'PROFESOR',
        'account_status': 'ACTIVO',
    }
)
if created:
    profesor1.set_password('profesor123')
    profesor1.save()
print(f"✅ Profesor: {profesor1.get_full_name()}")

# Profesor 2
profesor2, created = CustomUser.objects.get_or_create(
    email="profesor2@universidad.edu.pe",
    defaults={
        'username': 'profesor2@universidad.edu.pe',
        'first_name': 'María',
        'last_name': 'González',
        'user_role': 'PROFESOR',
        'account_status': 'ACTIVO',
    }
)
if created:
    profesor2.set_password('profesor123')
    profesor2.save()
print(f"✅ Profesor: {profesor2.get_full_name()}")

# Alumnos
alumnos = []
nombres = ['Juan', 'Ana', 'Pedro', 'Lucía', 'Diego', 'Sofia', 'Carlos', 'Elena']
apellidos = ['Pérez', 'García', 'López', 'Martínez', 'Rodríguez', 'Fernández', 'Silva', 'Torres']

for i in range(8):
    alumno, created = CustomUser.objects.get_or_create(
        email=f"alumno{i+1}@universidad.edu.pe",
        defaults={
            'username': f'alumno{i+1}@universidad.edu.pe',
            'first_name': nombres[i],
            'last_name': apellidos[i],
            'user_role': 'ALUMNO',
            'account_status': 'ACTIVO',
        }
    )
    if created:
        alumno.set_password('alumno123')
        alumno.save()
    alumnos.append(alumno)
    print(f"✅ Alumno: {alumno.get_full_name()}")

# 3. CREAR CURSOS
print("\n Creando cursos...")

# Curso 1: Programación I
curso1, created = Course.objects.get_or_create(
    course_code="CS101",
    defaults={
        'semester': semester,
        'course_name': 'Programación I',
        'credits': 4,
        'cycle': 3,
        'course_type': 'TEORIA'
    }
)
print(f"✅ Curso: {curso1.course_name}")

# Curso 2: Base de Datos
curso2, created = Course.objects.get_or_create(
    course_code="CS201",
    defaults={
        'semester': semester,
        'course_name': 'Base de Datos',
        'credits': 4,
        'cycle': 4,
        'course_type': 'TEORIA'
    }
)
print(f"✅ Curso: {curso2.course_name}")

# Curso 3: Algoritmos
curso3, created = Course.objects.get_or_create(
    course_code="CS102",
    defaults={
        'semester': semester,
        'course_name': 'Algoritmos y Estructura de Datos',
        'credits': 3,
        'cycle': 3,
        'course_type': 'TEORIA'
    }
)
print(f"✅ Curso: {curso3.course_name}")

# 4. CREAR GRUPOS
print("\n Creando grupos de curso...")

# Grupo Curso 1
grupo1, created = CourseGroup.objects.get_or_create(
    group_code="CS101-A",
    course=curso1,
    defaults={
        'capacity': 30,
        'day_of_week': 'LUNES',
        'start_time': time(8, 0),
        'end_time': time(10, 0),
        'room': 'Aula 201',
        'professor': profesor1
    }
)
print(f"✅ Grupo: {grupo1.group_code}")

# Grupo Curso 2
grupo2, created = CourseGroup.objects.get_or_create(
    group_code="CS201-A",
    course=curso2,
    defaults={
        'capacity': 30,
        'day_of_week': 'MARTES',
        'start_time': time(10, 0),
        'end_time': time(12, 0),
        'room': 'Aula 202',
        'professor': profesor2
    }
)
print(f"✅ Grupo: {grupo2.group_code}")

# Grupo Curso 3
grupo3, created = CourseGroup.objects.get_or_create(
    group_code="CS102-A",
    course=curso3,
    defaults={
        'capacity': 30,
        'day_of_week': 'MIERCOLES',
        'start_time': time(14, 0),
        'end_time': time(16, 0),
        'room': 'Aula 203',
        'professor': profesor1
    }
)
print(f"✅ Grupo: {grupo3.group_code}")

# 5. CREAR LABORATORIOS
print("\n🔬 Creando laboratorios...")

# Labs para Curso 1
lab1a, created = LaboratoryGroup.objects.get_or_create(
    course=curso1,
    lab_nomenclature="A",
    defaults={
        'capacity': 15,
        'day_of_week': 'MIERCOLES',
        'start_time': time(8, 0),
        'end_time': time(10, 0),
        'room': 'Lab 301',
        'professor': profesor1
    }
)
print(f"✅ Lab: {curso1.course_code} - Lab {lab1a.lab_nomenclature}")

lab1b, created = LaboratoryGroup.objects.get_or_create(
    course=curso1,
    lab_nomenclature="B",
    defaults={
        'capacity': 15,
        'day_of_week': 'JUEVES',
        'start_time': time(10, 0),
        'end_time': time(12, 0),
        'room': 'Lab 301',
        'professor': profesor1
    }
)
print(f"✅ Lab: {curso1.course_code} - Lab {lab1b.lab_nomenclature}")

# Labs para Curso 2
lab2a, created = LaboratoryGroup.objects.get_or_create(
    course=curso2,
    lab_nomenclature="A",
    defaults={
        'capacity': 15,
        'day_of_week': 'VIERNES',
        'start_time': time(8, 0),
        'end_time': time(10, 0),
        'room': 'Lab 302',
        'professor': profesor2
    }
)
print(f"✅ Lab: {curso2.course_code} - Lab {lab2a.lab_nomenclature}")

# 6. CREAR EVALUACIONES
print("\n Creando evaluaciones...")

# Evaluaciones para Curso 1
evaluaciones_curso1 = [
    {'name': 'Práctica Calificada 1', 'eval_type': 'CONTINUA', 'unit': 1, 'percentage': 20},
    {'name': 'Examen Parcial 1', 'eval_type': 'EXAMEN', 'unit': 1, 'percentage': 30},
    {'name': 'Práctica Calificada 2', 'eval_type': 'CONTINUA', 'unit': 2, 'percentage': 20},
    {'name': 'Examen Parcial 2', 'eval_type': 'EXAMEN', 'unit': 2, 'percentage': 30},
]

for eval_data in evaluaciones_curso1:
    eval_obj, created = Evaluation.objects.get_or_create(
        course=curso1,
        name=eval_data['name'],
        defaults={
            'evaluation_type': eval_data['eval_type'],
            'unit': eval_data['unit'],
            'percentage': Decimal(eval_data['percentage'])
        }
    )
    print(f"✅ Evaluación: {eval_obj.name}")

# Evaluaciones para Curso 2
evaluaciones_curso2 = [
    {'name': 'Laboratorio 1', 'eval_type': 'CONTINUA', 'unit': 1, 'percentage': 15},
    {'name': 'Examen Parcial 1', 'eval_type': 'EXAMEN', 'unit': 1, 'percentage': 35},
    {'name': 'Laboratorio 2', 'eval_type': 'CONTINUA', 'unit': 2, 'percentage': 15},
    {'name': 'Examen Parcial 2', 'eval_type': 'EXAMEN', 'unit': 2, 'percentage': 35},
]

for eval_data in evaluaciones_curso2:
    eval_obj, created = Evaluation.objects.get_or_create(
        course=curso2,
        name=eval_data['name'],
        defaults={
            'evaluation_type': eval_data['eval_type'],
            'unit': eval_data['unit'],
            'percentage': Decimal(eval_data['percentage'])
        }
    )
    print(f"✅ Evaluación: {eval_obj.name}")

# 7. MATRICULAR ALUMNOS
print("\n Matriculando alumnos...")

# Matricular primeros 6 alumnos en Curso 1
for i in range(6):
    enrollment, created = StudentEnrollment.objects.get_or_create(
        student=alumnos[i],
        course=curso1,
        defaults={
            'group': grupo1,
            'status': 'ACTIVO'
        }
    )
    print(f"✅ Matrícula: {alumnos[i].get_full_name()} en {curso1.course_code}")

# Matricular primeros 4 alumnos en Curso 2
for i in range(4):
    enrollment, created = StudentEnrollment.objects.get_or_create(
        student=alumnos[i],
        course=curso2,
        defaults={
            'group': grupo2,
            'status': 'ACTIVO'
        }
    )
    print(f"✅ Matrícula: {alumnos[i].get_full_name()} en {curso2.course_code}")

# Matricular alumnos 4-7 en Curso 3
for i in range(4, 8):
    enrollment, created = StudentEnrollment.objects.get_or_create(
        student=alumnos[i],
        course=curso3,
        defaults={
            'group': grupo3,
            'status': 'ACTIVO'
        }
    )
    print(f"✅ Matrícula: {alumnos[i].get_full_name()} en {curso3.course_code}")

# 8. REGISTRAR ALGUNAS NOTAS
print("\n Registrando notas de ejemplo...")

# Obtener evaluaciones
eval_pc1_curso1 = Evaluation.objects.get(course=curso1, name='Práctica Calificada 1')
eval_ep1_curso1 = Evaluation.objects.get(course=curso1, name='Examen Parcial 1')

# Notas para los primeros 3 alumnos del curso 1
notas = [
    {'alumno_idx': 0, 'nota_pc1': 15.5, 'nota_ep1': 14.0},
    {'alumno_idx': 1, 'nota_pc1': 12.0, 'nota_ep1': 11.5},
    {'alumno_idx': 2, 'nota_pc1': 16.5, 'nota_ep1': 15.0},
]

for nota_data in notas:
    enrollment = StudentEnrollment.objects.get(
        student=alumnos[nota_data['alumno_idx']],
        course=curso1
    )
    
    # Práctica Calificada
    grade1, created = GradeRecord.objects.get_or_create(
        enrollment=enrollment,
        evaluation=eval_pc1_curso1,
        defaults={
            'raw_score': Decimal(nota_data['nota_pc1']),
            'recorded_by': profesor1
        }
    )
    
    # Examen Parcial
    grade2, created = GradeRecord.objects.get_or_create(
        enrollment=enrollment,
        evaluation=eval_ep1_curso1,
        defaults={
            'raw_score': Decimal(nota_data['nota_ep1']),
            'recorded_by': profesor1
        }
    )
    
    print(f"✅ Notas registradas para: {alumnos[nota_data['alumno_idx']].get_full_name()}")

# 9. REGISTRAR ASISTENCIAS
print("\n Registrando asistencias de ejemplo...")

# Asistencias para el alumno 1 en curso 1 (5 sesiones)
enrollment_alumno1 = StudentEnrollment.objects.get(student=alumnos[0], course=curso1)
estados = ['P', 'P', 'F', 'P', 'P']  # 4 presentes, 1 falta

for sesion in range(1, 6):
    attendance, created = AttendanceRecord.objects.get_or_create(
        enrollment=enrollment_alumno1,
        session_number=sesion,
        defaults={
            'session_date': date.today() - timedelta(days=30-sesion*5),
            'status': estados[sesion-1],
            'professor_ip': '127.0.0.1',
            'recorded_by': profesor1
        }
    )

# Calcular porcentaje
enrollment_alumno1.calculate_attendance_percentage()
print(f"✅ Asistencias registradas para: {alumnos[0].get_full_name()} - {enrollment_alumno1.current_attendance_percentage}%")

print("\n" + "=" * 50)
print("✅ DATOS DE PRUEBA CARGADOS EXITOSAMENTE")
print("=" * 50)
print("\n CREDENCIALES DE ACCESO:")
print("\n PROFESORES:")
print("   Email: profesor1@universidad.edu.pe")
print("   Password: profesor123")
print("\n   Email: profesor2@universidad.edu.pe")
print("   Password: profesor123")
print("\n  ALUMNOS:")
print("   Email: alumno1@universidad.edu.pe")
print("   Password: alumno123")
print("   (alumno2, alumno3... hasta alumno8)")
print("\n" + "=" * 50)