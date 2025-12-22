import pytest
from django.db import IntegrityError
from tests.factories import StudentFactory, ProfessorFactory


@pytest.mark.django_db
class TestCustomUserModel:
    """Tests para el modelo CustomUser - Validaciones de negocio"""

    def test_user_creation_with_email_as_username(self):
        """
        Verifica que el email se use automáticamente como username
        cuando no se proporciona uno explícito.
        """
        # Arrange & Act
        user = StudentFactory.create(email="alumno@unsa.edu.pe", username="")

        # Assert
        assert user.username == "alumno@unsa.edu.pe"
        assert user.email == "alumno@unsa.edu.pe"

    def test_email_must_be_unique(self):
        """
        Verifica que no se puedan crear dos usuarios con el mismo email.
        Regla de negocio: Email es identificador único.
        """
        # Arrange
        email = "duplicado@unsa.edu.pe"
        StudentFactory.create(email=email)

        # Act & Assert
        with pytest.raises(IntegrityError):
            StudentFactory.create(email=email)

    def test_user_role_assignment(self):
        """
        Verifica que los roles se asignen correctamente
        y sean distinguibles entre tipos de usuario.
        """
        # Arrange & Act
        student = StudentFactory.create()
        professor = ProfessorFactory.create()

        # Assert
        assert student.user_role == "ALUMNO"
        assert professor.user_role == "PROFESOR"
        assert student.user_role != professor.user_role

    def test_user_full_name_display(self):
        """
        Verifica que el método __str__ retorne el formato esperado.
        """
        # Arrange
        user = StudentFactory.create(
            first_name="Juan",
            last_name="Pérez"
        )

        # Act
        display_name = str(user)

        # Assert
        assert "Juan Pérez" in display_name
        assert "Alumno" in display_name

    def test_default_account_status_is_active(self):
        """
        Verifica que el estado por defecto de la cuenta sea ACTIVO.
        """
        # Arrange & Act
        user = StudentFactory.create()

        # Assert
        assert user.account_status == "ACTIVO"

    def test_failed_login_attempts_counter(self):
        """
        Verifica que el contador de intentos fallidos funcione correctamente.
        """
        # Arrange
        user = StudentFactory.create()
        assert user.failed_login_attempts == 0

        # Act
        user.failed_login_attempts += 1
        user.save()

        # Assert
        user.refresh_from_db()
        assert user.failed_login_attempts == 1