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
    user_role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='ALUMNO')
    
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
    
    # Campo para usar email como username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # username será autogenerado
    
    class Meta:
        db_table = 'users'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_user_role_display()})"
    
    def save(self, *args, **kwargs):
        # Si no tiene username, usar el email
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)


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
        verbose_name = 'Semestre'
        verbose_name_plural = 'Semestres'
    
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
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'
        ordering = ['cycle', 'course_code']
    
    def __str__(self):
        return f"{self.course_code} - {self.course_name}"

class Classroom(models.Model):
    """Salón/Ambiente físico"""
    classroom_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    capacity = models.IntegerField()
    location = models.CharField(max_length=200)
    classroom_type = models.CharField(max_length=20, choices=[
        ('AULA', 'Aula'),
        ('LABORATORIO', 'Laboratorio'),
    ])
    equipment = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'classrooms'
        verbose_name = 'Salón'
        verbose_name_plural = 'Salones'
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class CourseGroup(models.Model):
    """Grupo de curso (teoría)"""
    group_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='groups')
    group_code = models.CharField(max_length=20)
    capacity = models.IntegerField()
    
    # Horario
    DAY_CHOICES = [
        ('LUNES', 'Lunes'),
        ('MARTES', 'Martes'),
        ('MIERCOLES', 'Miércoles'),
        ('JUEVES', 'Jueves'),
        ('VIERNES', 'Viernes'),
        ('SABADO', 'Sábado'),
    ]
    day_of_week = models.CharField(max_length=20, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.ForeignKey(Classroom, on_delete=models.PROTECT, null=True, blank=True, related_name='course_groups')
    
    professor = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='groups_taught', limit_choices_to={'user_role': 'PROFESOR'})
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'course_groups'
        unique_together = [['course', 'group_code']]
        verbose_name = 'Grupo de Curso'
        verbose_name_plural = 'Grupos de Curso'
    
    def __str__(self):
        return f"{self.course.course_code} - {self.group_code}"


class LaboratoryGroup(models.Model):
    """Grupo de laboratorio"""
    lab_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='laboratories')
    lab_nomenclature = models.CharField(max_length=5)  # A, B, C
    capacity = models.IntegerField()
    
    # Horario
    DAY_CHOICES = [
        ('LUNES', 'Lunes'),
        ('MARTES', 'Martes'),
        ('MIERCOLES', 'Miércoles'),
        ('JUEVES', 'Jueves'),
        ('VIERNES', 'Viernes'),
        ('SABADO', 'Sábado'),
    ]
    day_of_week = models.CharField(max_length=20, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.ForeignKey(Classroom, on_delete=models.PROTECT, null=True, blank=True, related_name='lab_groups')
    
    professor = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='labs_taught', limit_choices_to={'user_role': 'PROFESOR'})
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'laboratory_groups'
        unique_together = [['course', 'lab_nomenclature']]
        verbose_name = 'Grupo de Laboratorio'
        verbose_name_plural = 'Grupos de Laboratorio'
    
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
        verbose_name = 'Evaluación'
        verbose_name_plural = 'Evaluaciones'
        ordering = ['unit', 'name']
    
    def __str__(self):
        return f"{self.course.course_code} - {self.name}"


class Syllabus(models.Model):
    """Sílabo del curso"""
    syllabus_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.OneToOneField(Course, on_delete=models.CASCADE, related_name='syllabus')
    loaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'syllabuses'
        verbose_name = 'Sílabo'
        verbose_name_plural = 'Sílabos'
    
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
        verbose_name = 'Sesión de Sílabo'
        verbose_name_plural = 'Sesiones de Sílabo'
    
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
        verbose_name = 'Campaña de Matrícula Lab'
        verbose_name_plural = 'Campañas de Matrícula Lab'
    
    def __str__(self):
        return f"Campaña {self.course.course_code}"


class StudentPostulation(models.Model):
    """Postulación de estudiante a laboratorio"""
    postulation_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    campaign = models.ForeignKey(LabEnrollmentCampaign, on_delete=models.CASCADE, related_name='postulations')
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='lab_postulations', limit_choices_to={'user_role': 'ALUMNO'})
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
        verbose_name = 'Postulación Lab'
        verbose_name_plural = 'Postulaciones Lab'
    
    def __str__(self):
        return f"{self.student.get_full_name()} -> Lab {self.lab_group.lab_nomenclature}"


class LabAssignment(models.Model):
    """Asignación de laboratorio a estudiante"""
    assignment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    postulation = models.OneToOneField(StudentPostulation, on_delete=models.CASCADE, related_name='assignment')
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='lab_assignments', limit_choices_to={'user_role': 'ALUMNO'})
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
        verbose_name = 'Asignación Lab'
        verbose_name_plural = 'Asignaciones Lab'
    
    def __str__(self):
        return f"{self.student.get_full_name()} asignado a Lab {self.lab_group.lab_nomenclature}"


# ==================== ACADEMIC PERFORMANCE CONTEXT ====================

class StudentEnrollment(models.Model):
    """Matrícula de estudiante en curso"""
    enrollment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='enrollments', limit_choices_to={'user_role': 'ALUMNO'})
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    group = models.ForeignKey(CourseGroup, on_delete=models.SET_NULL, null=True, blank=True, related_name='enrollments')
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
        verbose_name = 'Matrícula'
        verbose_name_plural = 'Matrículas'
    
    def __str__(self):
        return f"{self.student.get_full_name()} en {self.course.course_code}"
    
    def calculate_attendance_percentage(self):
        """Calcula el porcentaje de asistencia"""
        total = self.attendance_records.count()
        if total == 0:
            return 0
        present = self.attendance_records.filter(status__in=['P', 'J']).count()
        percentage = (present / total) * 100
        self.current_attendance_percentage = round(percentage, 2)
        self.save()
        return self.current_attendance_percentage


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
        verbose_name = 'Registro de Asistencia'
        verbose_name_plural = 'Registros de Asistencia'
        ordering = ['session_number']
    
    def __str__(self):
        return f"Asistencia Sesión {self.session_number} - {self.enrollment.student.get_full_name()}"


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
        verbose_name = 'Registro de Nota'
        verbose_name_plural = 'Registros de Notas'
    
    def __str__(self):
        return f"{self.enrollment.student.get_full_name()} - {self.evaluation.name}: {self.rounded_score}"
    
    def save(self, *args, **kwargs):
        # Redondear automáticamente
        if self.raw_score >= int(self.raw_score) + 0.5:
            self.rounded_score = int(self.raw_score) + 1
        else:
            self.rounded_score = int(self.raw_score)
        super().save(*args, **kwargs)


class SubstitutoryExamEnrollment(models.Model):
    """Inscripción a examen sustitutorio"""
    exam_enrollment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='substitutory_exams', limit_choices_to={'user_role': 'ALUMNO'})
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='substitutory_exams')
    
    unit_to_replace = models.IntegerField()  # 1 o 2
    enrolled_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'substitutory_exam_enrollments'
        unique_together = [['student', 'course']]
        verbose_name = 'Inscripción Examen Sustitutorio'
        verbose_name_plural = 'Inscripciones Examen Sustitutorio'
    
    def __str__(self):
        return f"{self.student.get_full_name()} - Sustitutorio Unidad {self.unit_to_replace}"


class SubstitutoryGradeRecord(models.Model):
    """Nota de examen sustitutorio"""
    record_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exam_enrollment = models.OneToOneField(SubstitutoryExamEnrollment, on_delete=models.CASCADE, related_name='grade_record')
    
    score = models.DecimalField(max_digits=4, decimal_places=2)
    recorded_at = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='substitutory_grades_created')
    
    class Meta:
        db_table = 'substitutory_grade_records'
        verbose_name = 'Nota Examen Sustitutorio'
        verbose_name_plural = 'Notas Examen Sustitutorio'
    
    def __str__(self):
        return f"Sustitutorio {self.exam_enrollment.student.get_full_name()}: {self.score}"


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
        verbose_name = 'Log de Auditoría'
        verbose_name_plural = 'Logs de Auditoría'
    
    def __str__(self):
        return f"{self.timestamp} - {self.user} - {self.action}"