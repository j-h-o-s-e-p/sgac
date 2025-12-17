import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Max

# --- IMPORTACIONES DE MI CAPA DE DOMINIO ---
# Traigo mis reglas de negocio para no tenerlas hardcodeadas aquí
from domain.shared.constants import DAY_CHOICES
from domain.identity.constants import ROLE_CHOICES, USER_STATUS_CHOICES
from domain.academic_structure.constants import (
    COURSE_TYPE_CHOICES, CLASSROOM_TYPE_CHOICES, EVALUATION_TYPE_CHOICES,
    POSTULATION_STATUS_CHOICES, ASSIGNMENT_METHOD_CHOICES,
    ENROLLMENT_STATUS_CHOICES, ATTENDANCE_STATUS_CHOICES
)

# ==================== IDENTIDAD Y USUARIOS ====================

class CustomUser(AbstractUser):
    """
    Mi usuario personalizado. Uso UUID para que sea más seguro y el email
    como identificador principal en lugar del username.
    """
    user_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    email = models.EmailField(unique=True, verbose_name='Email Institucional')
    
    # Para cuando piden recuperar contraseña
    temporal_password = models.CharField(max_length=255, blank=True, null=True)
    temporal_password_expires_at = models.DateTimeField(blank=True, null=True)
    
    # Aquí uso las constantes que definí en el dominio
    user_role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='ALUMNO')
    account_status = models.CharField(max_length=20, choices=USER_STATUS_CHOICES, default='INACTIVO')
    
    # Seguridad básica
    failed_login_attempts = models.IntegerField(default=0)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Le digo a Django que use el email para loguear
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_user_role_display()})"
    
    def save(self, *args, **kwargs):
        # Si no me pasan username, uso el email por defecto
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)


class ExternalProfessor(models.Model):
    """
    Profes que vienen de fuera solo a dictar laboratorios. 
    No entran al sistema, solo necesito sus datos.
    """
    external_prof_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=200, verbose_name='Nombre Completo')
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    specialization = models.CharField(max_length=200, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'external_professors'
        verbose_name = 'Profesor Externo'
        verbose_name_plural = 'Profesores Externos'
    
    def __str__(self):
        return self.full_name


# ==================== ESTRUCTURA ACADÉMICA ====================

class Semester(models.Model):
    semester_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50) # Ej: 2025-1
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'semesters'
        ordering = ['-start_date']
        verbose_name = 'Semestre'
        verbose_name_plural = 'Semestres'
    
    def __str__(self):
        return self.name


class Course(models.Model):
    course_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Relación con semestre: si borro semestre, chau cursos
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='courses')
    course_code = models.CharField(max_length=20, unique=True)
    course_name = models.CharField(max_length=200)
    credits = models.IntegerField()
    cycle = models.IntegerField()
    
    # Uso mis constantes de dominio
    course_type = models.CharField(max_length=20, choices=COURSE_TYPE_CHOICES)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'courses'
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'
        ordering = ['cycle', 'course_code']
    
    def __str__(self):
        return f"{self.course_code} - {self.course_name}"


class Classroom(models.Model):
    classroom_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=10, unique=True, editable=False, blank=True, verbose_name="Código")
    name = models.CharField(max_length=100)
    capacity = models.IntegerField()
    location = models.CharField(max_length=200)
    classroom_type = models.CharField(max_length=20, choices=CLASSROOM_TYPE_CHOICES)
    equipment = models.TextField(blank=True) # Proyector, PC, etc.
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'classrooms'
        verbose_name = 'Salón'
        verbose_name_plural = 'Salones'

    def save(self, *args, **kwargs):
        # Lógica para autogenerar códigos tipo A001, A002...
        if not self.code:
            prefix = "A"
            last_obj = self.__class__.objects.aggregate(max_code=Max('code'))
            max_code = last_obj.get('max_code')
            new_num = 1
            if max_code:
                try:
                    last_num_str = max_code.replace(prefix, '')
                    if last_num_str.isdigit():
                        new_num = int(last_num_str) + 1
                except ValueError:
                    pass 
            self.code = f"{prefix}{new_num:03d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.name}"


class CourseGroup(models.Model):
    """Son las secciones, ej: Grupo A, Grupo B"""
    group_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='groups')
    group_code = models.CharField(max_length=20)
    capacity = models.IntegerField()
    # Solo puede ser un usuario con rol PROFESOR
    professor = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='groups_taught', limit_choices_to={'user_role': 'PROFESOR'}
    )
    
    # Flags para saber si secretaría ya cargó los alumnos
    students_loaded = models.BooleanField(default=False)
    last_student_upload_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'course_groups' 
        unique_together = [['course', 'group_code']] # No puede haber dos grupos 'A' en el mismo curso
        verbose_name = 'Grupo de Curso'
        verbose_name_plural = 'Grupos de Curso'
        ordering = ['course__course_code', 'group_code'] 
    
    def __str__(self):
        return f"{self.course.course_code} - {self.group_code}"


class Schedule(models.Model):
    """Horarios de teoría"""
    schedule_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course_group = models.ForeignKey(CourseGroup, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.CharField(max_length=20, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.ForeignKey(Classroom, on_delete=models.SET_NULL, null=True, blank=True, related_name='schedules')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'schedules' 
        verbose_name = 'Bloque de Horario'
        verbose_name_plural = 'Bloques de Horario'
        unique_together = [['course_group', 'day_of_week', 'start_time']]
        ordering = ['day_of_week', 'start_time']

    def __str__(self):
        return f"{self.course_group} ({self.get_day_of_week_display()} {self.start_time}-{self.end_time})"


class LaboratoryGroup(models.Model):
    """Grupos específicos para labs (pueden tener otro profe)"""
    lab_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='laboratories')
    lab_nomenclature = models.CharField(max_length=5) # Ej: A, B, C
    capacity = models.IntegerField()
    
    day_of_week = models.CharField(max_length=20, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.ForeignKey(Classroom, on_delete=models.PROTECT, null=True, blank=True, related_name='lab_groups')
    
    # Puede ser profe del sistema o uno externo
    professor = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='labs_taught', limit_choices_to={'user_role': 'PROFESOR'}
    )
    external_professor = models.ForeignKey(
        'ExternalProfessor', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='labs_taught', verbose_name='Profesor Externo'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'laboratory_groups'
        unique_together = [['course', 'lab_nomenclature']]
        verbose_name = 'Grupo de Laboratorio'
        verbose_name_plural = 'Grupos de Laboratorio'
    
    def __str__(self):
        return f"{self.course.course_code} - Lab {self.lab_nomenclature}"
    
    def get_professor_name(self):
        # Helper para sacar el nombre sin importar de donde venga
        if self.professor:
            return self.professor.get_full_name()
        elif self.external_professor:
            return self.external_professor.full_name
        return "Sin asignar"


# ==================== SÍLABOS Y EVALUACIONES ====================

class Evaluation(models.Model):
    """Configuración de pesos y notas"""
    evaluation_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='evaluations')
    
    name = models.CharField(max_length=100) # Ej: Examen 1
    evaluation_type = models.CharField(max_length=20, choices=EVALUATION_TYPE_CHOICES)
    
    unit = models.IntegerField()
    percentage = models.DecimalField(max_digits=5, decimal_places=2) # Peso en nota final
    due_date = models.DateField(blank=True, null=True)
    order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'evaluations'
        verbose_name = 'Evaluación'
        verbose_name_plural = 'Evaluaciones'
        ordering = ['order', 'unit', 'name']
    
    def __str__(self):
        return f"{self.course.course_code} - {self.name} ({self.percentage}%)"


class Syllabus(models.Model):
    """El documento oficial del curso"""
    syllabus_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Un curso tiene UN solo sílabo activo
    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name='syllabus')
    syllabus_file = models.FileField(upload_to='syllabi/%Y/%m/', blank=True, null=True, verbose_name='PDF del Sílabo')
    
    # Metadata sacada automáticamente al leer el PDF
    credits_extracted = models.IntegerField(null=True, blank=True, verbose_name='Créditos extraídos')
    theory_hours = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    practice_hours = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    lab_hours = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    
    evaluations_configured = models.BooleanField(default=False, help_text="Indica si evaluaciones configuradas")
    loaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'syllabuses'
        verbose_name = 'Sílabo'
        verbose_name_plural = 'Sílabos'
    
    def __str__(self):
        return f"Sílabo {self.course.course_code}"
    
    def get_progress_percentage(self):
        # Calcula cuánto del sílabo se ha avanzado
        total_sessions = self.sessions.count()
        if total_sessions == 0:
            return 0
        completed_sessions = SessionProgress.objects.filter(
            session__syllabus=self,
            session__isnull=False
        ).count()
        return round((completed_sessions / total_sessions) * 100, 2)


class SyllabusUnit(models.Model):
    unit_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    syllabus = models.ForeignKey(Syllabus, on_delete=models.CASCADE, related_name='units')
    unit_number = models.IntegerField()
    unit_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'syllabus_units'
        unique_together = [['syllabus', 'unit_number']]
        ordering = ['unit_number']
        verbose_name = 'Unidad Temática'
        verbose_name_plural = 'Unidades Temáticas'
    
    def __str__(self):
        return f"Unidad {self.unit_number}: {self.unit_name}"


class SyllabusSession(models.Model):
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    syllabus = models.ForeignKey(Syllabus, on_delete=models.CASCADE, related_name='sessions')
    unit = models.ForeignKey(SyllabusUnit, on_delete=models.CASCADE, null=True, blank=True, related_name='sessions')
    
    session_number = models.IntegerField()
    week_number = models.IntegerField(null=True, blank=True)
    topic = models.TextField()
    
    planned_date = models.DateField(null=True, blank=True)
    real_date = models.DateField(null=True, blank=True, verbose_name="Fecha Real de Ejecución")
    
    accumulated_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'syllabus_sessions'
        ordering = ['session_number']
        verbose_name = 'Sesión de Sílabo'
        verbose_name_plural = 'Sesiones de Sílabo'
    
    def __str__(self):
        return f"Sesión {self.session_number} - {self.syllabus.course.course_code}"
    
    def is_completed(self):
        return hasattr(self, 'progress')


class SessionProgress(models.Model):
    """Marca qué profesor avanzó qué tema y cuándo"""
    progress_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.OneToOneField(SyllabusSession, on_delete=models.CASCADE, related_name='progress')
    course_group = models.ForeignKey(CourseGroup, on_delete=models.CASCADE, related_name='session_progress')
    
    completed_date = models.DateField()
    marked_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='sessions_marked')
    notes = models.TextField(blank=True, verbose_name='Observaciones')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'session_progress'
        verbose_name = 'Progreso de Sesión'
        verbose_name_plural = 'Progreso de Sesiones'
        ordering = ['completed_date']

# ==================== MATRÍCULA Y LABORATORIOS ====================

class LabEnrollmentCampaign(models.Model):
    """Periodo donde los alumnos pueden elegir sus laboratorios"""
    campaign_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lab_campaigns')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_closed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'lab_enrollment_campaigns'
        verbose_name = 'Campaña de Matrícula Lab'
        verbose_name_plural = 'Campañas de Matrícula Lab'

        indexes = [
            models.Index(
                fields=['course', 'is_closed'],
                name='campaign_course_closed_idx'
            )
        ]
    
    def __str__(self):
        return f"Campaña {self.course.course_code}"


class StudentPostulation(models.Model):
    """El alumno dice: 'Yo quiero este horario'"""
    postulation_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(LabEnrollmentCampaign, on_delete=models.CASCADE, related_name='postulations')
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='lab_postulations', limit_choices_to={'user_role': 'ALUMNO'})
    lab_group = models.ForeignKey(LaboratoryGroup, on_delete=models.CASCADE, related_name='postulations')
    timestamp = models.DateTimeField(auto_now_add=True)
    
    status = models.CharField(max_length=20, choices=POSTULATION_STATUS_CHOICES, default='PENDIENTE')
    
    class Meta:
        db_table = 'student_postulations'
        unique_together = [['campaign', 'student']]
        verbose_name = 'Postulación Lab'
        verbose_name_plural = 'Postulaciones Lab'
        ordering = ['timestamp']

        indexes = [
            models.Index(
                fields=['campaign', 'lab_group', 'status'],
                name='postul_campaign_lab_status_idx'
            )
        ]


class LabAssignment(models.Model):
    """El resultado final: Tú te quedas en este lab"""
    assignment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    postulation = models.OneToOneField(StudentPostulation, on_delete=models.CASCADE, related_name='assignment')
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='lab_assignments', limit_choices_to={'user_role': 'ALUMNO'})
    lab_group = models.ForeignKey(LaboratoryGroup, on_delete=models.CASCADE, related_name='assignments')
    
    assignment_method = models.CharField(max_length=20, choices=ASSIGNMENT_METHOD_CHOICES)
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'lab_assignments'
        unique_together = [['student', 'lab_group']]
        verbose_name = 'Asignación Lab'
        verbose_name_plural = 'Asignaciones Lab'

# ==================== RENDIMIENTO ACADÉMICO ====================

class StudentEnrollment(models.Model):
    """La matrícula oficial del alumno en un curso"""
    enrollment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='enrollments', limit_choices_to={'user_role': 'ALUMNO'})
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    group = models.ForeignKey(CourseGroup, on_delete=models.SET_NULL, null=True, blank=True, related_name='enrollments')
    lab_assignment = models.ForeignKey(LabAssignment, on_delete=models.SET_NULL, null=True, blank=True, related_name='enrollment')
    
    status = models.CharField(max_length=20, choices=ENROLLMENT_STATUS_CHOICES, default='ACTIVO')
    
    current_attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    final_grade = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'student_enrollments'
        unique_together = [['student', 'course']]
        verbose_name = 'Matrícula'
        verbose_name_plural = 'Matrículas'
    
    def __str__(self):
        return f"{self.student.get_full_name()} en {self.course.course_code}"
    
    def calculate_attendance_percentage(self):
        """
        Calcula y actualiza el porcentaje de asistencia.
        Lógica: Cuenta Presentes y Justificadas sobre el total.
        """
        total_sessions = self.attendance_records.count()
        
        if total_sessions > 0:
            attended = self.attendance_records.filter(status__in=['P', 'J']).count()
            percentage = (attended / total_sessions) * 100
            self.current_attendance_percentage = round(percentage, 2)
        else:
            self.current_attendance_percentage = 0
            
        self.save()
        return self.current_attendance_percentage

    def calculate_final_grade(self):
        """
        Calcula nota final basándose en los pesos de las evaluaciones.
        """
        evaluations = self.course.evaluations.all()
        grade_records = self.grade_records.filter(evaluation__in=evaluations).select_related('evaluation')
        
        final_grade = Decimal('0.00')
        if not evaluations.exists():
             self.final_grade = None
             self.save()
             return

        for evaluation in evaluations:
            # Busco si el alumno tiene nota en esta evaluación
            grade_record = next((gr for gr in grade_records if gr.evaluation_id == evaluation.evaluation_id), None)
            if grade_record and grade_record.rounded_score is not None:
                score = grade_record.rounded_score
                weight = evaluation.percentage / Decimal(100)
                final_grade += score * weight

        self.final_grade = round(final_grade, 2)
        self.save()
        return self.final_grade


class AttendanceRecord(models.Model):
    record_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.ForeignKey(StudentEnrollment, on_delete=models.CASCADE, related_name='attendance_records')
    session_number = models.IntegerField()
    session_date = models.DateField()
    
    status = models.CharField(max_length=1, choices=ATTENDANCE_STATUS_CHOICES)
    justification = models.TextField(blank=True)
    
    # Seguridad: guardo desde dónde marcó el profe
    professor_ip = models.GenericIPAddressField()
    geo_latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    geo_longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    
    recorded_at = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='attendance_records_created')
    
    class Meta:
        db_table = 'attendance_records'
        unique_together = [['enrollment', 'session_number']]
        verbose_name = 'Registro de Asistencia'
        verbose_name_plural = 'Registros de Asistencia'


class GradeRecord(models.Model):
    record_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.ForeignKey(StudentEnrollment, on_delete=models.CASCADE, related_name='grade_records')
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE, related_name='grade_records')
    is_locked = models.BooleanField(default=False)
    raw_score = models.DecimalField(max_digits=4, decimal_places=2)
    rounded_score = models.DecimalField(max_digits=4, decimal_places=2)
    
    recorded_at = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='grade_records_created')
    
    class Meta:
        db_table = 'grade_records'
        unique_together = [['enrollment', 'evaluation']]
        verbose_name = 'Registro de Nota'
        verbose_name_plural = 'Registros de Notas'
    
    def save(self, *args, **kwargs):
        # Lógica de redondeo: .5 sube al inmediato superior
        if self.raw_score >= int(self.raw_score) + 0.5:
            self.rounded_score = int(self.raw_score) + 1
        else:
            self.rounded_score = int(self.raw_score)
        super().save(*args, **kwargs)


# ==================== AUDITORÍA ====================

class AuditLog(models.Model):
    """El chismoso del sistema: guarda quién hizo qué"""
    log_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=200)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    details = models.JSONField(blank=True, null=True)
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
        verbose_name = 'Log de Auditoría'
        verbose_name_plural = 'Logs de Auditoría'
    
    def __str__(self):
        return f"{self.timestamp} - {self.user} - {self.action}"