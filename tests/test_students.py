import pytest
from tests.factories import StudentFactory


@pytest.mark.django_db
class TestStudentLogic:
    def test_student_creation_with_factory(self):
        """
        Prueba que demuestra el uso de FactoryBoy para generar alumnos
        con datos falsos pero realistas.
        """
        # Arrange
        students = StudentFactory.create_batch(10)

        # Assert
        assert len(students) == 10

        for student in students:
            assert student.user_role == "ALUMNO"
            assert student.email is not None
            assert "@" in student.email
            assert student.first_name
            assert student.last_name
