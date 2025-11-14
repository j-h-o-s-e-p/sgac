"""
Ejecutar:
docker compose run --rm web python manage.py shell < scripts/load_data_from_csv_auto.py
"""

import pandas as pd
from datetime import date, time
import ftfy
import re

from infrastructure.persistence.models import (
    CustomUser, Semester, Course, CourseGroup, Classroom
)

print("="*50)
print(" CARGANDO DATOS (SOLO PROFESORES, CURSOS Y GRUPOS) ")
print("="*50)

# --- 1. Crear semestre ---
semester, _ = Semester.objects.update_or_create(
    name="2024-2",
    defaults={'start_date': date(2024,8,1), 'end_date': date(2024,12,20), 'is_active': True}
)
print(f"✅ Semestre: {semester.name}")

# --- 2. Leer CSV de cursos/profesores ---
df_cursos = pd.read_csv('scripts/data/Curso_Profesor.csv', encoding='utf-8-sig')
ciclo_map = {'A': 1, 'B': 2, 'C': 3, 'D': 4}

try:
    aula_obj, created = Classroom.objects.get_or_create(
        name='Aula 101',
        defaults={'capacity': 50} 
    )
    if created:
        print(f"✅ Aula 'Aula 101' creada con capacidad 50")
    else:
        print(f"✅ Aula 'Aula 101' encontrada")

except Exception as e:
    print(f"ERROR: No se pudo obtener o crear el aula 'Aula 101'. Error: {e}")
    exit()

for idx, row in df_cursos.iterrows():
    correo = ftfy.fix_text(str(row['Correo UNSA']).strip())
    docente = ftfy.fix_text(str(row['Docentes']).strip())
    nombres_docente = docente.split()
    first_name = nombres_docente[0]
    last_name = nombres_docente[-1] if len(nombres_docente) > 1 else nombres_docente[0]

    profesor, _ = CustomUser.objects.update_or_create(
        email=correo,
        defaults={
            'username': correo,
            'first_name': first_name,
            'last_name': last_name,
            'user_role': 'PROFESOR',
            'account_status': 'ACTIVO',
        }
    )
    profesor.set_password('profesor123')
    profesor.save()

    ciclo_value = ciclo_map.get(str(row['Cicl']).strip(), 1)
    curso_code = str(row['Codigo']).strip()
    curso, _ = Course.objects.update_or_create(
        course_code=curso_code,
        defaults={
            'semester': semester,
            'course_name': ftfy.fix_text(str(row['Asignatura']).strip()),
            'credits': 3,
            'cycle': ciclo_value,
            'course_type': 'TEORIA'
        }
    )

    grupo_code = f"{curso_code}-{str(row['Grup']).strip()}"
    grupo, _ = CourseGroup.objects.update_or_create(
        group_code=grupo_code,
        course=curso,
        defaults={
            'capacity': 30,
            'day_of_week': 'LUNES',
            'start_time': time(8,0),
            'end_time': time(10,0),
            'room': aula_obj,
            'professor': profesor
        }
    )
    print(f"✅ Profesor y grupo: {profesor.email} -> {curso.course_name} - {grupo.group_code}")


print("="*50)
print("✅ DATOS CARGADOS (SOLO PROFESORES, CURSOS Y GRUPOS)")
print("Contraseñas: Profesores = 'profesor123'")
print("="*50)