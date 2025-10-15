from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid


# ==================== IDENTITY CONTEXT ====================

class CustomUser(AbstractUser):
    """
    Usuario extendido del sistema.
    Mapeado desde domain.identity.User
    """
    user_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    email = models.EmailField(unique=True, verbose_name='Email Institucional')
    temporal_password = models.CharField(max_length=255, blank=True, null=True)
    temporal_password_expires_at = models.DateTimeField(blank=True, null=True)
    
    ROLE_CHOICES = [
        ('ADMIN', 'Administrador'),
        ('PROFESOR', 'Profesor'),
        ('ALUMNO', 'Alumno'),
        ('SECRETARIA', 'Secretaría'),
    ]
    user_role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    
    STATUS_CHOICES = [
        ('INACTIVO', 'Inactivo'),
        ('ACTIVO', 'Activo'),
        ('BLOQUEADO', 'Bloqueado'),
    ]
    account_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='INACTIVO')
    
    failed_login_attempts = models.IntegerField(default=0)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
    
    def __str__(self):
        return f"{self.email} ({self.user_role})"


# ==================== ACADEMIC STRUCTURE CONTEXT ====================

class Semester(models.Model):
    """Semestre académico"""
    semester_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)  # Ej: "2024-1"
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'semesters'
        ordering = ['-start_date']
    
    def __str__(self):
        return self.name


class Course(models.Model):
    """Curso"""
    course_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='courses')
    course_code = models.CharField(max_length=20, unique=True)
    course_name = models.CharField(max_length=200)
    credits = models.IntegerField()
    cycle = models.IntegerField()  # 1-10
    
    COURSE_TYPE_CHOICES = [
        ('TEORIA', 'Teoría'),
        ('PRACTICA', 'Práctica'),
    ]
    course_type = models.CharField(max_length=20, choices=COURSE_TYPE_CHOICES)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'courses'
    
    def __str__(self):
        return f"{self.course_code} - {self.course_name}"


class CourseGroup(models.Model):
    """Grupo de curso (teoría)"""
    group_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='groups')
    group_code = models.CharField(max_length=20)
    capacity = models.IntegerField()
    
    # Horario
    day_of_week = models.CharField(max_length=20)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50)
    
    professor = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='groups_taught')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'course_groups'
        unique_together = [['course', 'group_code']]
    
    def __str__(self):
        return f"{self.course.course_code} - {self.group_code}"


class LaboratoryGroup(models.Model):
    """Grupo de laboratorio"""
    lab_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='laboratories')
    lab_nomenclature = models.CharField(max_length=5)  # A, B, C
    capacity = models.IntegerField()
    
    # Horario
    day_of_week = models.CharField(max_length=20)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50)
    
    professor = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='labs_taught')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'laboratory_groups'
        unique_together = [['course', 'lab_nomenclature']]
    
    def __str__(self):
        return f"{self.course.course_code} - Lab {self.lab_nomenclature}"


class Evaluation(models.Model):
    """Evaluación de curso"""
    evaluation_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='evaluations')
    
    name = models.CharField(max_length=100)
    
    EVALUATION_TYPE_CHOICES = [
        ('CONTINUA', 'Evaluación Continua'),
        ('EXAMEN', 'Examen'),
    ]
    evaluation_type = models.CharField(max_length=20, choices=EVALUATION_TYPE_CHOICES)
    
    unit = models.IntegerField()  # 1, 2, 3
    percentage = models.DecimalField(max_digits=5, decimal_places=2)  # 0-100
    due_date = models.DateField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'evaluations'
    
    def __str__(self):
        return f"{self.course.course_code} - {self.name}"


class Syllabus(models.Model):
    """Sílabo del curso"""
    syllabus_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name='syllabus')
    loaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'syllabuses'
    
    def __str__(self):
        return f"Sílabo {self.course.course_code}"


class SyllabusSession(models.Model):
    """Sesión del sílabo"""
    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    syllabus = models.ForeignKey(Syllabus, on_delete=models.CASCADE, related_name='sessions')
    session_number = models.IntegerField()
    topic = models.TextField()
    planned_date = models.DateField()
    real_date = models.DateField(blank=True, null=True)
    observations = models.TextField(blank=True)
    
    class Meta:
        db_table = 'syllabus_sessions'
        ordering = ['session_number']
    
    def __str__(self):
        return f"Sesión {self.session_number} - {self.syllabus.course.course_code}"


# ==================== LAB ENROLLMENT CONTEXT ====================

class LabEnrollmentCampaign(models.Model):
    """Campaña de matrícula de laboratorios"""
    campaign_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lab_campaigns')
    
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_closed = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'lab_enrollment_campaigns'
    
    def __str__(self):
        return f"Campaña {self.course.course_code}"


class StudentPostulation(models.Model):
    """Postulación de estudiante a laboratorio"""
    postulation_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(LabEnrollmentCampaign, on_delete=models.CASCADE, related_name='postulations')
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='lab_postulations')
    lab_group = models.ForeignKey(LaboratoryGroup, on_delete=models.CASCADE, related_name='postulations')
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    STATUS_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('ASIGNADO', 'Asignado'),
        ('NO_ASIGNADO', 'No Asignado'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDIENTE')
    
    class Meta:
        db_table = 'student_postulations'
        unique_together = [['campaign', 'student']]
    
    def __str__(self):
        return f"{self.student.email} -> Lab {self.lab_group.lab_nomenclature}"


class LabAssignment(models.Model):
    """Asignación de laboratorio a estudiante"""
    assignment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    postulation = models.OneToOneField(StudentPostulation, on_delete=models.CASCADE, related_name='assignment')
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='lab_assignments')
    lab_group = models.ForeignKey(LaboratoryGroup, on_delete=models.CASCADE, related_name='assignments')
    
    ASSIGNMENT_METHOD_CHOICES = [
        ('AUTOMATIC', 'Automático'),
        ('LOTTERY', 'Sorteo'),
    ]
    assignment_method = models.CharField(max_length=20, choices=ASSIGNMENT_METHOD_CHOICES)
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'lab_assignments'
        unique_together = [['student', 'lab_group']]
    
    def __str__(self):
        return f"{self.student.email} asignado a Lab {self.lab_group.lab_nomenclature}"


# ==================== ACADEMIC PERFORMANCE CONTEXT ====================

class StudentEnrollment(models.Model):
    """Matrícula de estudiante en curso"""
    enrollment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    lab_assignment = models.ForeignKey(LabAssignment, on_delete=models.SET_NULL, null=True, blank=True, related_name='enrollment')
    
    STATUS_CHOICES = [
        ('ACTIVO', 'Activo'),
        ('RETIRADO', 'Retirado'),
        ('COMPLETADO', 'Completado'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVO')
    
    current_attendance_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    final_grade = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True)
    
    enrolled_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'student_enrollments'
        unique_together = [['student', 'course']]
    
    def __str__(self):
        return f"{self.student.email} en {self.course.course_code}"


class AttendanceRecord(models.Model):
    """Registro de asistencia"""
    record_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.ForeignKey(StudentEnrollment, on_delete=models.CASCADE, related_name='attendance_records')
    session_number = models.IntegerField()
    session_date = models.DateField()
    
    STATUS_CHOICES = [
        ('P', 'Presente'),
        ('F', 'Falta'),
        ('J', 'Falta Justificada'),
    ]
    status = models.CharField(max_length=1, choices=STATUS_CHOICES)
    justification = models.TextField(blank=True)
    
    professor_ip = models.GenericIPAddressField()
    geo_latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    geo_longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    
    recorded_at = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='attendance_records_created')
    
    class Meta:
        db_table = 'attendance_records'
        unique_together = [['enrollment', 'session_number']]
    
    def __str__(self):
        return f"Asistencia Sesión {self.session_number} - {self.enrollment.student.email}"


class GradeRecord(models.Model):
    """Registro de nota"""
    record_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.ForeignKey(StudentEnrollment, on_delete=models.CASCADE, related_name='grade_records')
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE, related_name='grade_records')
    
    raw_score = models.DecimalField(max_digits=4, decimal_places=2)  # 0-20
    rounded_score = models.DecimalField(max_digits=4, decimal_places=2)  # 0-20
    
    recorded_at = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='grade_records_created')
    
    class Meta:
        db_table = 'grade_records'
        unique_together = [['enrollment', 'evaluation']]
    
    def __str__(self):
        return f"{self.enrollment.student.email} - {self.evaluation.name}: {self.rounded_score}"


class SubstitutoryExamEnrollment(models.Model):
    """Inscripción a examen sustitutorio"""
    exam_enrollment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='substitutory_exams')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='substitutory_exams')
    
    unit_to_replace = models.IntegerField()  # 1 o 2
    enrolled_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'substitutory_exam_enrollments'
        unique_together = [['student', 'course']]
    
    def __str__(self):
        return f"{self.student.email} - Sustitutorio Unidad {self.unit_to_replace}"


class SubstitutoryGradeRecord(models.Model):
    """Nota de examen sustitutorio"""
    record_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exam_enrollment = models.OneToOneField(SubstitutoryExamEnrollment, on_delete=models.CASCADE, related_name='grade_record')
    
    score = models.DecimalField(max_digits=4, decimal_places=2)
    recorded_at = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='substitutory_grades_created')
    
    class Meta:
        db_table = 'substitutory_grade_records'
    
    def __str__(self):
        return f"Sustitutorio {self.exam_enrollment.student.email}: {self.score}"


# ==================== AUDITORÍA ====================

class AuditLog(models.Model):
    """Log de auditoría"""
    log_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=200)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    details = models.JSONField(blank=True, null=True)
    
    class Meta:
        db_table = 'audit_logs'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.timestamp} - {self.user} - {self.action}"
