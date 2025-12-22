import factory
from faker import Faker
from datetime import datetime, timedelta
from decimal import Decimal
from infrastructure.persistence.models import (
    CustomUser,
    Semester,
    Course,
    CourseGroup,
    StudentEnrollment,
    Evaluation,
    GradeRecord,
    Classroom,
    LaboratoryGroup,
)

fake = Faker("es_ES")


# ==================== USUARIOS ====================


class CustomUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CustomUser
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"user{n}@unsa.edu.pe")
    username = factory.LazyAttribute(lambda obj: obj.email)
    first_name = factory.LazyAttribute(lambda _: fake.first_name())
    last_name = factory.LazyAttribute(lambda _: fake.last_name())

    user_role = "ALUMNO"
    account_status = "ACTIVO"

    password = factory.PostGenerationMethodCall("set_password", "password123")


class StudentFactory(CustomUserFactory):
    """Alias semántico para crear estudiantes"""

    user_role = "ALUMNO"


class ProfessorFactory(CustomUserFactory):
    """Factory para profesores"""

    user_role = "PROFESOR"
    email = factory.Sequence(lambda n: f"profesor{n}@unsa.edu.pe")


# ==================== ESTRUCTURA ACADÉMICA ====================


class SemesterFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Semester

    name = factory.LazyAttribute(lambda _: f"{datetime.now().year}-1")
    start_date = factory.LazyAttribute(lambda _: datetime.now().date())
    end_date = factory.LazyAttribute(lambda obj: obj.start_date + timedelta(days=120))
    is_active = True


class CourseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Course

    semester = factory.SubFactory(SemesterFactory)
    course_code = factory.Sequence(lambda n: f"IS{n:03d}")
    course_name = factory.LazyAttribute(lambda obj: f"Curso {obj.course_code}")
    credits = 4
    cycle = 5
    course_type = "TEORIA_PRACTICA"


class ClassroomFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Classroom

    name = factory.Sequence(lambda n: f"Aula {n}")
    capacity = 30
    location = "Edificio A"
    classroom_type = "TEORIA"
    is_active = True


class CourseGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CourseGroup

    course = factory.SubFactory(CourseFactory)
    group_code = "A"
    capacity = 30
    professor = factory.SubFactory(ProfessorFactory)
    students_loaded = False


class LaboratoryGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LaboratoryGroup

    course = factory.SubFactory(CourseFactory)
    lab_nomenclature = factory.Sequence(lambda n: chr(65 + n))  # A, B, C...
    capacity = 20
    day_of_week = "LUNES"
    start_time = "08:00"
    end_time = "10:00"
    room = factory.SubFactory(ClassroomFactory)
    professor = factory.SubFactory(ProfessorFactory)


# ==================== EVALUACIONES ====================


class EvaluationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Evaluation

    course = factory.SubFactory(CourseFactory)
    name = factory.Sequence(lambda n: f"Examen {n}")
    evaluation_type = "EXAMEN"
    unit = 1
    percentage = Decimal("20.00")
    order = factory.Sequence(lambda n: n)


# ==================== MATRÍCULAS Y NOTAS ====================


class StudentEnrollmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StudentEnrollment

    student = factory.SubFactory(StudentFactory)
    course = factory.SubFactory(CourseFactory)
    group = factory.SubFactory(CourseGroupFactory)
    status = "ACTIVO"
    current_attendance_percentage = Decimal("0.00")


class GradeRecordFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = GradeRecord

    enrollment = factory.SubFactory(StudentEnrollmentFactory)
    evaluation = factory.SubFactory(EvaluationFactory)
    raw_score = Decimal("15.50")
    rounded_score = Decimal("16.00")
    is_locked = False
    recorded_by = factory.SubFactory(ProfessorFactory)
