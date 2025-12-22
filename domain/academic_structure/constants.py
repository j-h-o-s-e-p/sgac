# Tipos de cursos
COURSE_TYPE_CHOICES = [("TEORIA", "Teoría"), ("PRACTICA", "Práctica")]

# Tipos de aulas disponibles
CLASSROOM_TYPE_CHOICES = [("AULA", "Aula"), ("LABORATORIO", "Laboratorio")]

# Tipos de evaluación
EVALUATION_TYPE_CHOICES = [
    ("CONTINUA", "Evaluación Continua"),
    ("EXAMEN", "Examen Parcial"),
]

# Estados de la postulación a laboratorio
POSTULATION_STATUS_CHOICES = [
    ("PENDIENTE", "Pendiente"),
    ("ASIGNADO", "Asignado"),
    ("NO_ASIGNADO", "No Asignado"),
]

# Formas de asignar laboratorio
ASSIGNMENT_METHOD_CHOICES = [("AUTOMATIC", "Automático"), ("LOTTERY", "Sorteo")]

# Estado de la matrícula del alumno
ENROLLMENT_STATUS_CHOICES = [
    ("ACTIVO", "Activo"),
    ("RETIRADO", "Retirado"),
    ("COMPLETADO", "Completado"),
]

# Estados de asistencia
ATTENDANCE_STATUS_CHOICES = [
    ("P", "Presente"),
    ("F", "Falta"),
    ("J", "Falta Justificada"),
]
