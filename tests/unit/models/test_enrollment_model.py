import pytest
from decimal import Decimal
from django.db import IntegrityError
from tests.factories import (
    StudentEnrollmentFactory,
    GradeRecordFactory,
    EvaluationFactory,
    StudentFactory,
    CourseFactory,
)


@pytest.mark.django_db
class TestStudentEnrollmentModel:
    """Tests para matrícula y cálculo de notas - Lógica de negocio crítica"""

    def test_student_cannot_enroll_twice_in_same_course(self):
        """
        Verifica que un alumno no pueda matricularse dos veces en el mismo curso.
        Constraint: unique_together = [['student', 'course']]
        """
        # Arrange
        student = StudentFactory.create()
        course = CourseFactory.create()
        StudentEnrollmentFactory.create(student=student, course=course)

        # Act & Assert
        with pytest.raises(IntegrityError):
            StudentEnrollmentFactory.create(student=student, course=course)

    def test_calculate_final_grade_with_multiple_evaluations(self):
        """
        Verifica el cálculo correcto de la nota final ponderada.
        Caso: 3 evaluaciones con diferentes pesos.
        """
        # Arrange
        enrollment = StudentEnrollmentFactory.create()
        course = enrollment.course

        # Limpiar cualquier nota existente del factory
        enrollment.grade_records.all().delete()

        # Crear evaluaciones con sus pesos (deben sumar 100%)
        eval1 = EvaluationFactory.create(course=course, percentage=Decimal("30.00"))
        eval2 = EvaluationFactory.create(course=course, percentage=Decimal("30.00"))
        eval3 = EvaluationFactory.create(course=course, percentage=Decimal("40.00"))

        # Crear notas para el alumno
        GradeRecordFactory.create(
            enrollment=enrollment,
            evaluation=eval1,
            raw_score=Decimal("15.00"),
            rounded_score=Decimal("15.00"),
        )
        GradeRecordFactory.create(
            enrollment=enrollment,
            evaluation=eval2,
            raw_score=Decimal("18.00"),
            rounded_score=Decimal("18.00"),
        )
        GradeRecordFactory.create(
            enrollment=enrollment,
            evaluation=eval3,
            raw_score=Decimal("12.00"),
            rounded_score=Decimal("12.00"),
        )

        # Act
        final_grade = enrollment.calculate_final_grade()

        # Assert
        # El método devuelve float por usar round()
        # Convertimos a Decimal para comparar
        assert Decimal(str(final_grade)).quantize(Decimal("0.01")) == Decimal("14.70")

    def test_final_grade_is_none_when_no_evaluations_configured(self):
        """
        Verifica que la nota final sea None cuando no hay evaluaciones configuradas.
        """
        # Arrange
        enrollment = StudentEnrollmentFactory.create()

        # Act
        final_grade = enrollment.calculate_final_grade()

        # Assert
        assert final_grade is None

    def test_calculate_attendance_percentage_all_present(self):
        """
        Verifica el cálculo de asistencia cuando el alumno asistió a todas las clases.
        """
        # Arrange
        from tests.factories import StudentEnrollmentFactory
        from infrastructure.persistence.models import AttendanceRecord
        from datetime import date

        enrollment = StudentEnrollmentFactory.create()

        # Crear 10 registros de asistencia, todos presentes
        for i in range(1, 11):
            AttendanceRecord.objects.create(
                enrollment=enrollment,
                session_number=i,
                session_date=date.today(),
                status="P",  # Presente
                professor_ip="127.0.0.1",
            )

        # Act
        percentage = enrollment.calculate_attendance_percentage()

        # Assert
        assert percentage == Decimal("100.00")

    def test_calculate_attendance_percentage_with_absences(self):
        """
        Verifica el cálculo de asistencia con faltas.
        """
        # Arrange
        from infrastructure.persistence.models import AttendanceRecord
        from datetime import date

        enrollment = StudentEnrollmentFactory.create()

        # 7 presentes, 3 ausentes
        for i in range(1, 8):
            AttendanceRecord.objects.create(
                enrollment=enrollment,
                session_number=i,
                session_date=date.today(),
                status="P",
                professor_ip="127.0.0.1",
            )

        for i in range(8, 11):
            AttendanceRecord.objects.create(
                enrollment=enrollment,
                session_number=i,
                session_date=date.today(),
                status="F",  # Falta
                professor_ip="127.0.0.1",
            )

        # Act
        percentage = enrollment.calculate_attendance_percentage()

        # Assert
        assert percentage == Decimal("70.00")  # 7/10 = 70%
