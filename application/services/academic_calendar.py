from datetime import date, datetime, timedelta
from infrastructure.persistence.models import Schedule

def get_group_sessions(group):
    """
    Genera una lista de todas las sesiones programadas para un grupo
    basado en las fechas del semestre y el horario configurado.
    """
    # Obtenemos el semestre
    semester = group.course.semester
    start_date = semester.start_date
    end_date = semester.end_date
    
    # Obtenemos los horarios configurados (Ej: LUNES, MIERCOLES)
    schedules = group.schedules.all()
    
    # Mapeo de días de Python (0=Lunes) a tu modelo
    days_map = {
        0: 'LUNES', 1: 'MARTES', 2: 'MIERCOLES', 
        3: 'JUEVES', 4: 'VIERNES', 5: 'SABADO', 6: 'DOMINGO'
    }
    
    sessions = []
    current_date = start_date
    session_counter = 1
    
    # Iteramos día por día del semestre
    while current_date <= end_date:
        day_name = days_map[current_date.weekday()]
        
        # Buscamos si hay clase este día
        daily_schedule = next((s for s in schedules if s.day_of_week == day_name), None)
        
        if daily_schedule:
            sessions.append({
                'number': session_counter,
                'date': current_date,
                'day_name': day_name,
                'start_time': daily_schedule.start_time,
                'end_time': daily_schedule.end_time,
                'is_past': current_date < date.today(),
                'is_today': current_date == date.today(),
                'is_future': current_date > date.today()
            })
            session_counter += 1
            
        current_date += timedelta(days=1)
        
    return sessions