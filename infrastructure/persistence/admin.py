from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    CustomUser,Classroom, Semester, Course, CourseGroup, Schedule, LaboratoryGroup,
    Evaluation, Syllabus, SyllabusSession, LabEnrollmentCampaign,
    StudentPostulation, LabAssignment, StudentEnrollment,
    AttendanceRecord, GradeRecord, AuditLog
)

@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'user_role', 'account_status', 'is_active']
    list_filter = ['user_role', 'account_status', 'is_active', 'is_staff']
    search_fields = ['email', 'first_name', 'last_name', 'username']
    ordering = ['email']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información Personal', {'fields': ('first_name', 'last_name', 'username')}),
        ('Información del Sistema', {'fields': ('user_role', 'account_status', 'temporal_password', 'temporal_password_expires_at')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'user_role', 'password1', 'password2'),
        }),
    )

@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ['name', 'capacity', 'location']
    search_fields = ['name', 'location']
    ordering = ['name']

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'is_active']
    list_filter = ['is_active']
    ordering = ['-start_date']
    search_fields = ['name']

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['course_code', 'course_name', 'credits', 'cycle', 'course_type', 'semester']
    list_filter = ['cycle', 'course_type', 'semester']
    search_fields = ['course_code', 'course_name']
    ordering = ['cycle', 'course_code']

class ScheduleInline(admin.TabularInline):
    """
    Esto permite editar los Horarios (Schedule) 
    DENTRO de la página de su Grupo de Curso (CourseGroup).
    """
    model = Schedule

    fields = ('day_of_week', 'start_time', 'end_time', 'room')
    raw_id_fields = ('room',) 
    extra = 1 
    verbose_name = "Bloque de Horario"
    verbose_name_plural = "Bloques de Horario"


@admin.register(CourseGroup)
class CourseGroupAdmin(admin.ModelAdmin):
    """
    Admin para el "Grupo Lógico".
    """
    list_display = ('group_code', 'course', 'professor', 'capacity')
    list_filter = ('course__cycle', 'professor') 
    search_fields = ('group_code', 'course__course_name', 'professor__email')
    raw_id_fields = ('course', 'professor')
    
    inlines = [ScheduleInline]


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('course_group', 'day_of_week', 'start_time', 'end_time', 'room')
    list_filter = ('day_of_week', 'room')
    search_fields = (
        'course_group__course__course_name', 
        'course_group__group_code',
        'room__name'
    )
    raw_id_fields = ('course_group', 'room')

@admin.register(LaboratoryGroup)
class LaboratoryGroupAdmin(admin.ModelAdmin):
    list_display = ['lab_nomenclature', 'course', 'professor', 'capacity', 'day_of_week', 'start_time', 'end_time', 'room']
    list_filter = ['course', 'day_of_week']
    search_fields = ['lab_nomenclature', 'course__course_name', 'professor__email']
    raw_id_fields = ['course', 'professor']

@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ['name', 'course', 'evaluation_type', 'unit', 'percentage', 'due_date']
    list_filter = ['evaluation_type', 'unit', 'course']
    search_fields = ['name', 'course__course_name']
    raw_id_fields = ['course']

@admin.register(Syllabus)
class SyllabusAdmin(admin.ModelAdmin):
    list_display = ['course', 'loaded_at']
    search_fields = ['course__course_name']
    raw_id_fields = ['course']

@admin.register(SyllabusSession)
class SyllabusSessionAdmin(admin.ModelAdmin):
    list_display = ['session_number', 'syllabus', 'topic', 'planned_date', 'real_date']
    list_filter = ['planned_date']
    search_fields = ['topic', 'syllabus__course__course_name']
    raw_id_fields = ['syllabus']

@admin.register(LabEnrollmentCampaign)
class LabEnrollmentCampaignAdmin(admin.ModelAdmin):
    list_display = ['course', 'start_date', 'end_date', 'is_closed']
    list_filter = ['is_closed']
    search_fields = ['course__course_name']
    raw_id_fields = ['course']

@admin.register(StudentPostulation)
class StudentPostulationAdmin(admin.ModelAdmin):
    list_display = ['student', 'lab_group', 'campaign', 'status', 'timestamp']
    list_filter = ['status', 'campaign']
    search_fields = ['student__email', 'lab_group__lab_nomenclature']
    raw_id_fields = ['campaign', 'student', 'lab_group']

@admin.register(LabAssignment)
class LabAssignmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'lab_group', 'assignment_method', 'assigned_at']
    list_filter = ['assignment_method']
    search_fields = ['student__email', 'lab_group__lab_nomenclature']
    raw_id_fields = ['postulation', 'student', 'lab_group']

@admin.register(StudentEnrollment)
class StudentEnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'group', 'status', 'current_attendance_percentage', 'final_grade', 'enrolled_at']
    list_filter = ['status', 'course']
    search_fields = ['student__email', 'course__course_name']
    raw_id_fields = ['student', 'course', 'group', 'lab_assignment']
    readonly_fields = ['enrolled_at', 'updated_at']

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ['enrollment', 'session_number', 'session_date', 'status', 'recorded_by']
    list_filter = ['status', 'session_date']
    search_fields = ['enrollment__student__email']
    raw_id_fields = ['enrollment', 'recorded_by']
    readonly_fields = ['recorded_at']

@admin.register(GradeRecord)
class GradeRecordAdmin(admin.ModelAdmin):
    list_display = ['enrollment', 'evaluation', 'raw_score', 'rounded_score', 'recorded_by', 'recorded_at']
    list_filter = ['evaluation__unit']
    search_fields = ['enrollment__student__email', 'evaluation__name']
    raw_id_fields = ['enrollment', 'evaluation', 'recorded_by']
    readonly_fields = ['recorded_at', 'rounded_score']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'action', 'ip_address']
    list_filter = ['timestamp', 'action']
    search_fields = ['user__email', 'action']
    raw_id_fields = ['user']
    readonly_fields = ['timestamp']