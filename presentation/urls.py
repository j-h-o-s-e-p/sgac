from django.urls import path
from presentation.views import auth_views, student_views, professor_views

app_name = 'presentation'

urlpatterns = [
    # Autenticación
    path('', auth_views.login_view, name='login'),
    path('login/', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout_view, name='logout'),
    
    # Alumno
    path('alumno/dashboard/', student_views.dashboard, name='student_dashboard'),
    path('alumno/horario/', student_views.schedule, name='student_schedule'),
    path('alumno/notas/', student_views.grades, name='student_grades'),
    path('alumno/matricula-lab/', student_views.lab_enrollment, name='student_lab_enrollment'),
    
    # Profesor
    path('profesor/dashboard/', professor_views.dashboard, name='professor_dashboard'),
    path('profesor/asistencia/', professor_views.attendance, name='professor_attendance'),
    path('profesor/registrar-asistencia/<uuid:group_id>/', professor_views.record_attendance, name='professor_record_attendance'),
    path('profesor/notas/', professor_views.grades, name='professor_grades'),
    path('profesor/registrar-notas/<uuid:course_id>/', professor_views.record_grades, name='professor_record_grades'),
    path('profesor/horario/', professor_views.schedule, name='professor_schedule'),
]