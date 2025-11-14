from django.urls import path
from presentation.views import auth_views, student_views, professor_views, secretaria_views

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

    # Secretaría 
    path('secretaria/dashboard/', secretaria_views.SecretariaDashboardView.as_view(), name='secretaria_dashboard'),
    path('secretaria/salones/', secretaria_views.ClassroomListView.as_view(), name='secretaria_classrooms'),
    path('secretaria/salones/nuevo/', secretaria_views.ClassroomCreateView.as_view(), name='secretaria_classroom_add'),
    path('secretaria/salones/<uuid:pk>/editar/', secretaria_views.ClassroomUpdateView.as_view(), name='secretaria_classroom_edit'),
    path('secretaria/salones/<uuid:pk>/eliminar/', secretaria_views.ClassroomDeleteView.as_view(), name='secretaria_classroom_delete'),
    path('secretaria/programacion/', secretaria_views.CourseScheduleView.as_view(), name='secretaria_schedule'),
    path('secretaria/carga-masiva/', secretaria_views.BulkUploadView.as_view(), name='secretaria_upload'),
    path('secretaria/upload/cursos/', secretaria_views.upload_cursos_view, name='secretaria_upload_cursos'),
    path('secretaria/upload/alumnos/', secretaria_views.upload_alumnos_view, name='secretaria_upload_alumnos'),
]