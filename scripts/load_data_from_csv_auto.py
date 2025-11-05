"""
Script para cargar datos desde CSV y matricular alumnos automáticamente según CSV de origen
Ejecutar: docker compose run --rm web python manage.py shell < scripts/load_data_from_csv_auto.py
"""
import pandas as pd
from datetime import date, time
import ftfy  # pip install ftfy

from infrastructure.persistence.models import (
    CustomUser, Semester, Course, CourseGroup, StudentEnrollment, Evaluation
)

print("="*50)
print(" CARGANDO DATOS DESDE CSV (FINAL DETALLADO) ")
print("="*50)

# --- 1. Crear semestre ---
semester, created = Semester.objects.get_or_create(
    name="2024-2",
    defaults={'start_date': date(2024,8,1), 'end_date': date(2024,12,20), 'is_active': True}
)
print(f"✅ Semestre: {semester.name}")

# --- 2. Leer CSV de cursos/profesores ---
df_cursos = pd.read_csv('scripts/data/Curso_Profesor.csv', encoding='utf-8-sig')

# Crear cursos, grupos y profesores
curso_grupo_map = {}
ciclo_map = {'A': 1, 'B': 2, 'C': 3, 'D': 4}

for idx, row in df_cursos.iterrows():
    # PROFESOR
    correo = ftfy.fix_text(str(row['Correo UNSA']).strip())
    docente = ftfy.fix_text(str(row['Docentes']).strip())
    nombres_docente = docente.split()
    first_name = nombres_docente[0]
    last_name = nombres_docente[-1] if len(nombres_docente) > 1 else nombres_docente[0]

    profesor, created = CustomUser.objects.get_or_create(
        email=correo,
        defaults={
            'username': correo,
            'first_name': first_name,
            'last_name': last_name,
            'user_role': 'PROFESOR',
            'account_status': 'ACTIVO',
        }
    )
    if created:
        profesor.set_password('profesor123')
        profesor.save()

    # CURSO
    ciclo_value = ciclo_map.get(str(row['Cicl']).strip(), 1)
    curso_code = str(row['Codigo']).strip()
    curso, created = Course.objects.get_or_create(
        course_code=curso_code,
        defaults={
            'semester': semester,
            'course_name': ftfy.fix_text(str(row['Asignatura']).strip()),
            'credits': 3,
            'cycle': ciclo_value,
            'course_type': 'TEORIA'
        }
    )

    # GRUPO
    grupo_code = f"{curso_code}-{str(row['Grup']).strip()}"
    grupo, created = CourseGroup.objects.get_or_create(
        group_code=grupo_code,
        course=curso,
        defaults={
            'capacity': 30,
            'day_of_week': 'LUNES',  # valor por defecto
            'start_time': time(8,0),
            'end_time': time(10,0),
            'room': 'Aula 101',
            'professor': profesor
        }
    )
    curso_grupo_map[(curso_code, str(row['Grup']).strip())] = grupo
    print(f"✅ Curso y grupo: {curso.course_name} - {grupo.group_code}")

# --- 3. Leer CSV de alumnos y matricular ---
archivo_alumnos = [
    'scripts/data/Trabajo_Interdisciplinar_II_Ciclo_B_Grupo_B.csv',
    'scripts/data/Trabajo_Interdisciplinar_III_Ciclo_B_Grupo_A.csv'
]

for f in archivo_alumnos:
    import re
    match = re.search(r'(.+?)_Ciclo_(.+?)_Grupo_(.+?)\.csv', f.split('/')[-1])
    if match:
        ciclo = match.group(2)
        grupo_name = match.group(3)
    else:
        ciclo = "A"
        grupo_name = "A"

    df = pd.read_csv(f, encoding='utf-8-sig')

    # Ignorar la primera fila si es encabezado
    for idx, row in df.iterrows():
        # Nombre de alumno
        nombres_apellidos = ftfy.fix_text(str(row['Apellidos y Nombres']).strip()).split()
        if len(nombres_apellidos) > 1:
            first_name = nombres_apellidos[1]
            last_name = nombres_apellidos[0]
        else:
            first_name = nombres_apellidos[0]
            last_name = nombres_apellidos[0]

        # Usuario de alumno: inicial + apellido
        inicial = first_name[0].lower()
        usuario_email = f"{inicial}{last_name.lower()}@unsa.edu.pe"

        alumno, created = CustomUser.objects.get_or_create(
            email=usuario_email,
            defaults={
                'username': usuario_email,
                'first_name': first_name,
                'last_name': last_name,
                'user_role': 'ALUMNO',
                'account_status': 'ACTIVO',
            }
        )
        if created:
            alumno.set_password('alumno123')
            alumno.save()
        print(f"✅ Alumno: {alumno.get_full_name()} ({usuario_email})")

        # Asignar grupo
        grupo = None
        for (codigo, grp), g in curso_grupo_map.items():
            if grp == grupo_name:
                grupo = g
                break
        if grupo:
            enrollment, created = StudentEnrollment.objects.get_or_create(
                student=alumno,
                course=grupo.course,
                defaults={'group': grupo, 'status':'ACTIVO'}
            )
            print(f"✅ Matrícula: {alumno.get_full_name()} en {grupo.course.course_name} - {grupo.group_code}")
        else:
            print(f"⚠️ No se encontró grupo para {alumno.get_full_name()}")

    print(f"📊 Total alumnos procesados en {f}: {len(df)}")

# --- 4. Crear evaluaciones por defecto ---
for curso in Course.objects.filter(semester=semester):
    Evaluation.objects.get_or_create(
        course=curso,
        name="Examen Parcial 1",
        defaults={'evaluation_type':'EXAMEN','unit':1,'percentage':50}
    )
    Evaluation.objects.get_or_create(
        course=curso,
        name="Trabajo Práctico 1",
        defaults={'evaluation_type':'CONTINUA','unit':1,'percentage':50}
    )

print("="*50)
print("✅ DATOS CARGADOS DESDE CSV EXITOSAMENTE")
print("Contraseñas: Alumnos = 'alumno123', Profesores = 'profesor123'")
print("="*50)