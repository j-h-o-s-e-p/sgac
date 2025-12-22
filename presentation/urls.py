from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from .views import (
    auth_views,
    student_views,
    professor_views,
    secretaria_views,
    secretaria_lab_views,
    secretaria_statistics_views,
    secretaria_syllabus_views  
)

app_name = 'presentation'

urlpatterns = [   
    # --- AUTH ---
    path('', auth_views.login_view, name='login'),
    path('login/', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout_view, name='logout'),
    path('change-password/', auth_views.change_password_view, name='change_password'),

    # --- STUDENT ---
    path('student/dashboard/', student_views.dashboard, name='student_dashboard'),
    path('student/schedule/', student_views.schedule, name='student_schedule'),
    path('student/grades/', student_views.grades, name='student_grades'),
    path('student/syllabus/', student_views.syllabus_list, name='student_syllabus_list'),
    path('student/syllabus/<uuid:course_id>/', student_views.syllabus_detail, name='student_syllabus_detail'),
    path('student/attendance/', student_views.attendance_list, name='student_attendance_list'),
    path('student/attendance/<uuid:course_id>/', student_views.attendance_detail, name='student_attendance_detail'),

    # --- PROFESSOR ---
    path('professor/dashboard/', professor_views.dashboard, name='professor_dashboard'),
    path('professor/my-courses/', professor_views.my_courses, name='professor_my_courses'),
    path('professor/schedule/', professor_views.schedule, name='professor_schedule'),
    path('professor/statistics/', professor_views.statistics, name='professor_statistics'),
    path('professor/upload-syllabus/<uuid:course_id>/', professor_views.upload_syllabus, name='professor_upload_syllabus'),
    path('professor/attendance/record/<uuid:group_id>/', professor_views.record_attendance, name='professor_record_attendance'),
    path('professor/attendance/report/<uuid:group_id>/', professor_views.attendance_report, name='professor_attendance_report'),
    path('professor/grades/record/<uuid:group_id>/', professor_views.consolidated_grades, name='professor_record_grades'),
    path('professor/grades/<uuid:course_id>/upload-csv/', professor_views.upload_grades_csv, name='professor_upload_grades_csv'),
    path('professor/api/progress/<uuid:group_id>/', professor_views.get_course_progress_api, name='professor_progress_api'),

    # --- SECRETARÍA: DASHBOARD Y AULAS ---
    path('secretaria/dashboard/', secretaria_views.SecretariaDashboardView.as_view(), name='secretaria_dashboard'),
    path('secretaria/classrooms/', secretaria_views.ClassroomListView.as_view(), name='secretaria_classrooms'),
    path('secretaria/classrooms/new/', secretaria_views.ClassroomCreateView.as_view(), name='secretaria_classroom_add'),
    path('secretaria/classrooms/<uuid:pk>/edit/', secretaria_views.ClassroomUpdateView.as_view(), name='secretaria_classroom_edit'),
    path('secretaria/classrooms/<uuid:pk>/delete/', secretaria_views.ClassroomDeleteView.as_view(), name='secretaria_classroom_delete'),
    
    # --- SECRETARÍA: PROGRAMACIÓN ---
    path('secretaria/schedule/', secretaria_views.CourseScheduleView.as_view(), name='secretaria_schedule'),
    path('api/schedule/save/', secretaria_views.save_course_group_schedule, name='api_save_schedule'),
    
    # --- SECRETARÍA: CARGA Y REPORTES ---
    path('secretaria/bulk-upload/', secretaria_views.BulkUploadView.as_view(), name='secretaria_upload'),
    path('secretaria/upload/group/<uuid:group_id>/', secretaria_views.upload_students_to_group_view, name='secretaria_upload_students_to_group'),
    path('secretaria/reportes/notas/', secretaria_views.SecretariaGradeReportView.as_view(), name='secretaria_grade_report'),
    path('secretaria/reportes/notas/descargar/<uuid:group_id>/', secretaria_views.download_grades_excel, name='secretaria_download_grades'),

    # --- SECRETARÍA: SÍLABOS ---
    path('secretaria/syllabus/', secretaria_syllabus_views.SyllabusListView.as_view(), name='secretaria_syllabus_list'),
    path('secretaria/syllabus/process/<uuid:syllabus_id>/', secretaria_syllabus_views.ProcessSyllabusView.as_view(), name='secretaria_process_syllabus'),
    path('secretaria/syllabus/process-all/', secretaria_syllabus_views.ReprocessAllSyllabusesView.as_view(), name='secretaria_reprocess_all'),

    # --- SECRETARÍA: LABORATORIOS ---
    path('secretaria/laboratories/', secretaria_lab_views.LabManagementView.as_view(), name='secretaria_lab_management'),
    path('secretaria/laboratories/create/', secretaria_lab_views.CreateLabGroupView.as_view(), name='secretaria_lab_create'),
    path('secretaria/laboratories/<uuid:lab_id>/delete/', secretaria_lab_views.DeleteLabGroupView.as_view(), name='secretaria_lab_delete'),
    path('secretaria/laboratories/check-conflicts/', secretaria_lab_views.CheckScheduleConflictsView.as_view(), name='secretaria_lab_check_conflicts'),
    path('secretaria/laboratories/available-classrooms/', secretaria_lab_views.GetAvailableClassroomsView.as_view(), name='secretaria_lab_available_classrooms'),
    
    # --- SECRETARÍA: LABORATORIOS - CAMPAÑA DE INSCRIPCIÓN ---
    path('secretaria/laboratories/enable-enrollment/<uuid:course_id>/', 
         secretaria_lab_views.EnableLabEnrollmentView.as_view(), 
         name='secretaria_lab_enable_enrollment'),
    
    path('secretaria/laboratories/campaign-status/<uuid:course_id>/', 
         secretaria_lab_views.GetCampaignStatusView.as_view(), 
         name='secretaria_lab_campaign_status'),
    
    path('secretaria/laboratories/enrolled-students/<uuid:lab_id>/', 
         secretaria_lab_views.GetLabEnrolledStudentsView.as_view(), 
         name='secretaria_lab_enrolled_students'),
    
    path('secretaria/laboratories/close-enrollment/<uuid:course_id>/', 
         secretaria_lab_views.CloseLabEnrollmentView.as_view(), 
         name='secretaria_lab_close_enrollment'),

    # --- SECRETARÍA: ESTADÍSTICAS ---
    path('secretaria/statistics/', secretaria_statistics_views.SecretariaStatisticsView.as_view(), name='secretaria_statistics'),

    path('student/lab-enrollment/', student_views.lab_enrollment, name='student_lab_enrollment'),
        # AGREGAR ESTAS 2 NUEVAS RUTAS:
    path('student/lab-enrollment/postulate/', 
         student_views.postulate_to_lab, 
         name='student_lab_postulate'),
    
    path('student/lab-enrollment/details/<uuid:lab_id>/', 
         student_views.get_lab_details, 
         name='student_lab_details'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)