from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    CustomUser, ExternalProfessor, Classroom, Semester, Course, CourseGroup, Schedule, 
    LaboratoryGroup, Evaluation, Syllabus, SyllabusUnit, SyllabusSession, SessionProgress,
    LabEnrollmentCampaign, StudentPostulation, LabAssignment, StudentEnrollment,
    AttendanceRecord, GradeRecord, AuditLog
)

# ==================== USUARIOS ====================

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

@admin.register(ExternalProfessor)
class ExternalProfessorAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'specialization']
    search_fields = ['full_name', 'email']


# ==================== ESTRUCTURA ACADÉMICA ====================

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'is_active']
    list_filter = ['is_active']
    ordering = ['-start_date']

@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'capacity', 'classroom_type', 'is_active']
    list_filter = ['classroom_type', 'is_active']
    search_fields = ['name', 'code']

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['course_code', 'course_name', 'cycle', 'course_type', 'semester']
    list_filter = ['cycle', 'course_type', 'semester']
    search_fields = ['course_code', 'course_name']
    ordering = ['cycle', 'course_code']

# Inline para ver horarios dentro del grupo
class ScheduleInline(admin.TabularInline):
    model = Schedule
    fields = ('day_of_week', 'start_time', 'end_time', 'room')
    raw_id_fields = ('room',) 
    extra = 1 

@admin.register(CourseGroup)
class CourseGroupAdmin(admin.ModelAdmin):
    list_display = ('group_code', 'course', 'professor', 'capacity', 'students_loaded')
    list_filter = ('course__cycle', 'professor', 'students_loaded') 
    search_fields = ('group_code', 'course__course_name', 'professor__email')
    raw_id_fields = ('course', 'professor')
    inlines = [ScheduleInline]

@admin.register(LaboratoryGroup)
class LaboratoryGroupAdmin(admin.ModelAdmin):
    list_display = ['lab_nomenclature', 'course', 'professor', 'day_of_week', 'start_time']
    list_filter = ['day_of_week', 'course']
    search_fields = ['lab_nomenclature', 'course__course_name']
    raw_id_fields = ['course', 'professor', 'external_professor', 'room']


# ==================== SÍLABOS Y EVALUACIONES ====================

@admin.register(Evaluation)
class EvaluationAdmin(admin.ModelAdmin):
    list_display = ['course', 'name', 'evaluation_type', 'unit', 'percentage']
    list_filter = ['evaluation_type', 'unit']
    search_fields = ['course__course_name', 'name']
    raw_id_fields = ['course']

# Inline para ver Unidades dentro del Sílabo
class SyllabusUnitInline(admin.StackedInline):
    model = SyllabusUnit
    extra = 0

@admin.register(Syllabus)
class SyllabusAdmin(admin.ModelAdmin):
    list_display = ['course', 'credits_extracted', 'loaded_at', 'evaluations_configured']
    search_fields = ['course__course_name']
    raw_id_fields = ['course']
    inlines = [SyllabusUnitInline]

@admin.register(SyllabusUnit)
class SyllabusUnitAdmin(admin.ModelAdmin):
    list_display = ['syllabus', 'unit_number', 'unit_name']
    search_fields = ['unit_name']
    raw_id_fields = ['syllabus']

@admin.register(SyllabusSession)
class SyllabusSessionAdmin(admin.ModelAdmin):
    list_display = ['session_number', 'syllabus', 'unit', 'topic', 'planned_date', 'real_date']
    list_filter = ['planned_date', 'unit'] 
    search_fields = ['topic', 'syllabus__course__course_name']
    raw_id_fields = ['syllabus', 'unit']

@admin.register(SessionProgress)
class SessionProgressAdmin(admin.ModelAdmin):
    list_display = ['session', 'course_group', 'completed_date', 'marked_by']
    list_filter = ['completed_date']
    search_fields = ['session__topic', 'course_group__group_code', 'marked_by__email']
    raw_id_fields = ['session', 'course_group', 'marked_by']


# ==================== MATRÍCULA Y ASIGNACIONES ====================

@admin.register(LabEnrollmentCampaign)
class LabEnrollmentCampaignAdmin(admin.ModelAdmin):
    list_display = ['course', 'start_date', 'end_date', 'is_closed']
    list_filter = ['is_closed']
    raw_id_fields = ['course']

@admin.register(StudentPostulation)
class StudentPostulationAdmin(admin.ModelAdmin):
    list_display = ['student', 'campaign', 'lab_group', 'status', 'timestamp']
    list_filter = ['status']
    search_fields = ['student__email', 'campaign__course__course_name']
    raw_id_fields = ['campaign', 'student', 'lab_group']

@admin.register(LabAssignment)
class LabAssignmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'lab_group', 'assignment_method', 'assigned_at']
    list_filter = ['assignment_method']
    search_fields = ['student__email', 'lab_group__course__course_name']
    raw_id_fields = ['postulation', 'student', 'lab_group']


# ==================== RENDIMIENTO ACADÉMICO ====================

@admin.register(StudentEnrollment)
class StudentEnrollmentAdmin(admin.ModelAdmin):
    # Agregamos attendance percentage para verlo fácil
    list_display = ['student', 'course', 'group', 'status', 'final_grade', 'current_attendance_percentage']
    list_filter = ['status', 'course']
    search_fields = ['student__email', 'student__last_name', 'course__course_name']
    raw_id_fields = ['student', 'course', 'group', 'lab_assignment']

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ['enrollment', 'session_number', 'session_date', 'status']
    list_filter = ['status', 'session_date']
    search_fields = ['enrollment__student__email']
    raw_id_fields = ['enrollment', 'recorded_by']

@admin.register(GradeRecord)
class GradeRecordAdmin(admin.ModelAdmin):
    list_display = ['enrollment', 'evaluation', 'raw_score', 'rounded_score', 'is_locked']
    list_filter = ['is_locked', 'evaluation__unit']
    search_fields = ['enrollment__student__email']
    raw_id_fields = ['enrollment', 'evaluation', 'recorded_by']


# ==================== AUDITORÍA ====================

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'action', 'ip_address']
    list_filter = ['action', 'timestamp']
    search_fields = ['user__email', 'action', 'details']
    readonly_fields = ['timestamp', 'ip_address', 'details']

admin.site.register(Schedule)