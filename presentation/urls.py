from django.urls import path
from presentation.views import auth_views, student_views, professor_views, secretaria_views

app_name = 'presentation'

urlpatterns = [
    # --- Autenticación ---
    path('', auth_views.login_view, name='login'),
    path('login/', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout_view, name='logout'),
    
    # --- Módulo de Alumno (Estandarizado a /student/) ---
    path('student/dashboard/', student_views.dashboard, name='student_dashboard'),
    path('student/schedule/', student_views.schedule, name='student_schedule'),
    path('student/grades/', student_views.grades, name='student_grades'),
    path('student/lab-enrollment/', student_views.lab_enrollment, name='student_lab_enrollment'),
    path('student/syllabus/', student_views.syllabus_list, name='student_syllabus_list'),
    path('student/syllabus/<uuid:course_id>/', student_views.syllabus_detail, name='student_syllabus_detail'),
    path('student/attendance/', student_views.attendance_list, name='student_attendance_list'),
    path('student/attendance/<uuid:course_id>/', student_views.attendance_detail, name='student_attendance_detail'),
    
    # --- Módulo de Profesor ---
    path('professor/dashboard/', professor_views.dashboard, name='professor_dashboard'),
    path('professor/attendance/', professor_views.attendance, name='professor_attendance'),
    path('professor/attendance/record/<uuid:group_id>/', professor_views.record_attendance, name='professor_record_attendance'),
    path('professor/attendance/report/<uuid:group_id>/', professor_views.attendance_report, name='professor_attendance_report'),
    path('professor/grades/', professor_views.grades, name='professor_grades'),
    path('professor/grades/record/<uuid:course_id>/', professor_views.consolidated_grades, name='professor_record_grades'),
    path('professor/schedule/', professor_views.schedule, name='professor_schedule'),
    path('professor/grades/<uuid:course_id>/upload-csv/', professor_views.upload_grades_csv, name='professor_upload_grades_csv'),

    # --- Módulo de Secretaría ---
    path('secretaria/dashboard/', secretaria_views.SecretariaDashboardView.as_view(), name='secretaria_dashboard'),
    path('secretaria/classrooms/', secretaria_views.ClassroomListView.as_view(), name='secretaria_classrooms'),
    path('secretaria/classrooms/new/', secretaria_views.ClassroomCreateView.as_view(), name='secretaria_classroom_add'),
    path('secretaria/classrooms/<uuid:pk>/edit/', secretaria_views.ClassroomUpdateView.as_view(), name='secretaria_classroom_edit'),
    path('secretaria/classrooms/<uuid:pk>/delete/', secretaria_views.ClassroomDeleteView.as_view(), name='secretaria_classroom_delete'),
    path('secretaria/schedule/', secretaria_views.CourseScheduleView.as_view(), name='secretaria_schedule'),
    path('secretaria/bulk-upload/', secretaria_views.BulkUploadView.as_view(), name='secretaria_upload'),
    path('secretaria/upload/group/<uuid:group_id>/', secretaria_views.upload_students_to_group_view, name='secretaria_upload_students_to_group'),
    
    # APIs (Para AJAX/Fetch)
    path('api/schedule/save/', secretaria_views.save_course_group_schedule, name='api_save_schedule'),
]