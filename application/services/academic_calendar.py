from datetime import date, datetime, timedelta
from infrastructure.persistence.models import Schedule, Semester

# Constante auxiliar para mapear los strings de la BD a los enteros de Python (0=Lunes, 6=Domingo)
DAY_MAPPING = {
    'LUNES': 0,
    'MARTES': 1,
    'MIERCOLES': 2,
    'JUEVES': 3,
    'VIERNES': 4,
    'SABADO': 5,
    'DOMINGO': 6
}

def get_group_sessions(group):
    """
    Genera las sesiones de un grupo de curso basado en su horario semanal.
    """
    # Obtener todos los horarios del grupo
    schedules = Schedule.objects.filter(course_group=group).order_by('day_of_week', 'start_time')
    
    if not schedules.exists():
        return []
    
    # Obtener semestre
    semester = group.course.semester
    if not semester:
        return []
    
    start_date = semester.start_date
    end_date = semester.end_date
    
    # Recolectar todos los días de clase únicos (ej: [0, 2] para Lunes y Miércoles)
    class_days = set()
    for schedule in schedules:
        weekday = DAY_MAPPING.get(schedule.day_of_week)
        if weekday is not None:
            class_days.add(weekday)
    
    if not class_days:
        return []
    
    # Generar sesiones
    sessions = []
    current_date = start_date
    session_number = 1
    today = date.today()
    
    while current_date <= end_date:
        if current_date.weekday() in class_days:
            # Obtener nombre bonito del día
            # Buscamos la key (LUNES) basada en el value (0)
            day_name = next((k.capitalize() for k, v in DAY_MAPPING.items() if v == current_date.weekday()), current_date.strftime('%A'))
            
            sessions.append({
                'number': session_number,
                'date': current_date,
                'day_name': day_name,
                'is_today': current_date == today,
                'is_past': current_date < today,
                'is_future': current_date > today,
            })
            
            session_number += 1
        
        current_date += timedelta(days=1)
    
    return sessions

def get_lab_sessions(lab_group):
    """
    Genera las sesiones de un laboratorio.
    Regla de negocio: Los labs empiezan 1 semana después del inicio del semestre.
    """
    semester = lab_group.course.semester
    if not semester:
        return []
    
    # Lab empieza 1 semana después
    lab_start_date = semester.start_date + timedelta(days=7)
    lab_end_date = semester.end_date
    
    target_weekday = DAY_MAPPING.get(lab_group.day_of_week)
    if target_weekday is None:
        return []
    
    sessions = []
    current_date = lab_start_date
    session_number = 1
    today = date.today()
    
    # 1. Avanzar el calendario hasta encontrar el primer día que coincida (ej. el primer Jueves)
    while current_date.weekday() != target_weekday:
        current_date += timedelta(days=1)
    
    # 2. Generar sesiones saltando de 7 en 7 días
    while current_date <= lab_end_date:
        sessions.append({
            'number': session_number,
            'date': current_date,
            'day_name': lab_group.get_day_of_week_display(), # Django display method
            'is_today': current_date == today,
            'is_past': current_date < today,
            'is_future': current_date > today,
        })
        
        session_number += 1
        current_date += timedelta(days=7) 
    
    return sessions