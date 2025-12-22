import pytest
from decimal import Decimal
from tests.factories import GradeRecordFactory


@pytest.mark.django_db
class TestGradeRecordRounding:
    """
    Tests para la lógica de redondeo de notas.
    Regla de negocio: .5 o más redondea hacia arriba.
    """

    @pytest.mark.parametrize(
        "raw_score,expected_rounded",
        [
            (Decimal("15.00"), Decimal("15")),
            (Decimal("15.49"), Decimal("15")),
            (Decimal("15.50"), Decimal("16")),
            (Decimal("15.51"), Decimal("16")),
            (Decimal("15.99"), Decimal("16")),
            (Decimal("19.50"), Decimal("20")),
            (Decimal("10.49"), Decimal("10")),
        ],
    )
    def test_grade_rounding_logic(self, raw_score, expected_rounded):
        """
        Verifica que el redondeo de notas siga la regla:
        - De .00 a .49 -> Mantiene el entero
        - De .50 a .99 -> Sube al siguiente entero
        """
        # Arrange & Act
        grade = GradeRecordFactory.create(raw_score=raw_score)

        # Assert
        assert grade.rounded_score == expected_rounded

    def test_grade_record_has_creator(self):
        """
        Verifica que cada registro de nota tenga un profesor responsable.
        """
        # Arrange & Act
        grade = GradeRecordFactory.create()

        # Assert
        assert grade.recorded_by is not None
        assert grade.recorded_by.user_role == "PROFESOR"

    def test_grade_can_be_locked(self):
        """
        Verifica que las notas puedan bloquearse para evitar modificaciones.
        """
        # Arrange
        grade = GradeRecordFactory.create(is_locked=False)

        # Act
        grade.is_locked = True
        grade.save()

        # Assert
        grade.refresh_from_db()
        assert grade.is_locked is True
