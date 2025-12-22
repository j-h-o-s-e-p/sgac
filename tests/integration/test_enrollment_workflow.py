import pytest
from decimal import Decimal
from datetime import date
from tests.factories import (
    StudentFactory,
    CourseFactory,
    CourseGroupFactory,
    StudentEnrollmentFactory,
    EvaluationFactory,
    GradeRecordFactory,
    ProfessorFactory,
)
from infrastructure.persistence.models import AttendanceRecord


@pytest.mark.django_db
class TestCompleteEnrollmentWorkflow:
    """
    Tests de integración que simulan el flujo completo
    desde la matrícula hasta la nota final.
    """

    def test_complete_student_academic_cycle(self):
        """
        Test integral: Simula el ciclo académico completo de un estudiante.

        Flujo:
        1. Alumno se matricula en curso
        2. Profesor registra asistencias
        3. Profesor registra evaluaciones
        4. Sistema calcula nota final y porcentaje de asistencia
        """
        # ============ FASE 1: MATRÍCULA ============
        student = StudentFactory.create(first_name="María", last_name="González")
        professor = ProfessorFactory.create(
            first_name="Dr. Carlos", last_name="Rodríguez"
        )
        course = CourseFactory.create(
            course_code="IS101", course_name="Ingeniería de Software I"
        )
        group = CourseGroupFactory.create(course=course, professor=professor)

        enrollment = StudentEnrollmentFactory.create(
            student=student, course=course, group=group, status="ACTIVO"
        )

        # ============ FASE 2: CONFIGURAR EVALUACIONES ============
        eval_parcial = EvaluationFactory.create(
            course=course, name="Examen Parcial", percentage=Decimal("30.00")
        )
        eval_final = EvaluationFactory.create(
            course=course, name="Examen Final", percentage=Decimal("40.00")
        )
        eval_practicas = EvaluationFactory.create(
            course=course, name="Prácticas", percentage=Decimal("30.00")
        )

        # ============ FASE 3: REGISTRAR ASISTENCIAS ============
        # Simular 12 sesiones: 10 presentes, 2 faltas
        for session in range(1, 11):
            AttendanceRecord.objects.create(
                enrollment=enrollment,
                session_number=session,
                session_date=date.today(),
                status="P",  # Presente
                professor_ip="127.0.0.1",
                recorded_by=professor,
            )

        for session in range(11, 13):
            AttendanceRecord.objects.create(
                enrollment=enrollment,
                session_number=session,
                session_date=date.today(),
                status="F",  # Falta
                professor_ip="127.0.0.1",
                recorded_by=professor,
            )

        # ============ FASE 4: REGISTRAR NOTAS ============
        GradeRecordFactory.create(
            enrollment=enrollment,
            evaluation=eval_parcial,
            raw_score=Decimal("16.50"),  # Se redondeará a 17
            recorded_by=professor,
        )
        GradeRecordFactory.create(
            enrollment=enrollment,
            evaluation=eval_final,
            raw_score=Decimal("14.00"),
            recorded_by=professor,
        )
        GradeRecordFactory.create(
            enrollment=enrollment,
            evaluation=eval_practicas,
            raw_score=Decimal("18.50"),  # Se redondeará a 19
            recorded_by=professor,
        )

        # ============ FASE 5: CÁLCULOS FINALES ============
        attendance_pct = enrollment.calculate_attendance_percentage()
        final_grade = enrollment.calculate_final_grade()

        # ============ ASSERTIONS ============
        # Helper function para convertir a Decimal de forma segura
        def to_decimal(value, default=None):
            from decimal import Decimal, InvalidOperation

            if value is None:
                return default
            if isinstance(value, Decimal):
                return value.quantize(Decimal("0.01"))
            try:
                return Decimal(str(value)).quantize(Decimal("0.01"))
            except (InvalidOperation, TypeError):
                return default

        # Verificar asistencia: 10/12 = 83.33%
        attendance_decimal = to_decimal(attendance_pct)
        assert attendance_decimal == Decimal(
            "83.33"
        ), f"Esperado 83.33, obtenido {attendance_decimal}"

        # Verificar nota final: (17*0.30) + (14*0.40) + (19*0.30) = 16.40
        final_grade_decimal = to_decimal(final_grade)
        assert final_grade_decimal == Decimal(
            "16.40"
        ), f"Esperado 16.40, obtenido {final_grade_decimal}"

        # Verificar estado de matrícula
        enrollment.refresh_from_db()

        # Verificar campos en la base de datos
        assert enrollment.status == "ACTIVO"

        # Verificar porcentaje de asistencia en BD
        db_attendance = to_decimal(enrollment.current_attendance_percentage)
        assert db_attendance == Decimal(
            "83.33"
        ), f"En BD: Esperado 83.33, obtenido {db_attendance}"

        # Verificar nota final en BD
        db_final_grade = to_decimal(enrollment.final_grade)
        assert db_final_grade == Decimal(
            "16.40"
        ), f"En BD: Esperado 16.40, obtenido {db_final_grade}"

        # Opcional: Verificar con tolerancia pequeña para floats
        def assert_decimal_equal(actual, expected, tolerance=Decimal("0.01")):
            """Compara decimales con cierta tolerancia para floats"""
            actual_dec = to_decimal(actual)
            expected_dec = to_decimal(expected)
            difference = abs(actual_dec - expected_dec)
            assert (
                difference <= tolerance
            ), f"Esperado {expected_dec}, obtenido {actual_dec} (diferencia: {difference})"

        # Usar esta función para mayor robustez
        assert_decimal_equal(attendance_pct, Decimal("83.33"))
        assert_decimal_equal(final_grade, Decimal("16.40"))
        assert_decimal_equal(enrollment.current_attendance_percentage, Decimal("83.33"))
        assert_decimal_equal(enrollment.final_grade, Decimal("16.40"))

    def test_student_fails_course_due_to_low_attendance(self):
        """
        Verifica que un estudiante con baja asistencia tenga el porcentaje correcto.
        Aunque no repruebe automáticamente, el sistema debe calcular correctamente.
        """
        # Arrange
        enrollment = StudentEnrollmentFactory.create()
        professor = ProfessorFactory.create()

        # Solo asiste a 4 de 10 clases (40%)
        for session in range(1, 5):
            AttendanceRecord.objects.create(
                enrollment=enrollment,
                session_number=session,
                session_date=date.today(),
                status="P",
                professor_ip="127.0.0.1",
                recorded_by=professor,
            )

        for session in range(5, 11):
            AttendanceRecord.objects.create(
                enrollment=enrollment,
                session_number=session,
                session_date=date.today(),
                status="F",
                professor_ip="127.0.0.1",
                recorded_by=professor,
            )

        # Act
        attendance = enrollment.calculate_attendance_percentage()

        # Assert
        assert attendance == Decimal("40.00")
        assert attendance < Decimal("70.00")  # Umbral típico de asistencia mínima
