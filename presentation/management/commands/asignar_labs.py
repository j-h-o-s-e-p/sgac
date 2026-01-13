from django.core.management.base import BaseCommand
from django.db import transaction
from infrastructure.persistence.models import (
    StudentEnrollment,
    LaboratoryGroup,
    StudentPostulation,
    LabAssignment,
    LabEnrollmentCampaign,
    Schedule,
)


class Command(BaseCommand):
    help = "Matricula automáticamente a todos los alumnos en laboratorios sin cruce de horario"

    def handle(self, *args, **kwargs):
        self.stdout.write(
            self.style.WARNING("Iniciando asignación masiva de laboratorios...")
        )

        stats = {
            "assigned": 0,
            "skipped_no_campaign": 0,
            "skipped_conflict": 0,
            "skipped_full": 0,
            "skipped_already_assigned": 0,
        }

        # Obtener todas las matrículas activas SIN laboratorio asignado
        enrollments = StudentEnrollment.objects.filter(
            status="ACTIVO", lab_assignment__isnull=True
        ).select_related("student", "course", "group")

        for enrollment in enrollments:
            # Verificar si hay campaña activa para este curso
            campaign = LabEnrollmentCampaign.objects.filter(
                course=enrollment.course, is_closed=False
            ).first()

            if not campaign:
                stats["skipped_no_campaign"] += 1
                continue

            # Buscar laboratorios disponibles del curso
            labs = LaboratoryGroup.objects.filter(course=enrollment.course).order_by(
                "lab_nomenclature"
            )

            assigned = False
            for lab in labs:
                # 1. Verificar cupos
                current_count = StudentPostulation.objects.filter(
                    campaign=campaign, lab_group=lab
                ).count()

                if current_count >= lab.capacity:
                    continue

                # 2. Verificar conflicto de horario
                if self._has_schedule_conflict(enrollment.student, lab):
                    continue

                # 3. Asignar
                try:
                    with transaction.atomic():
                        # Crear postulación
                        postulation = StudentPostulation.objects.create(
                            campaign=campaign,
                            student=enrollment.student,
                            lab_group=lab,
                            status="ACEPTADO",
                        )

                        # Crear asignación
                        assignment = LabAssignment.objects.create(
                            postulation=postulation,
                            student=enrollment.student,
                            lab_group=lab,
                            assignment_method="DIRECTO",
                        )

                        # Actualizar matrícula
                        enrollment.lab_assignment = assignment
                        enrollment.save()

                        stats["assigned"] += 1
                        assigned = True
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✓ {enrollment.student.get_full_name()} → "
                                f"{enrollment.course.course_code} Lab {lab.lab_nomenclature}"
                            )
                        )
                        break

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error asignando: {str(e)}"))

            if not assigned:
                if self._all_labs_full(campaign, labs):
                    stats["skipped_full"] += 1
                else:
                    stats["skipped_conflict"] += 1

        # Resumen
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 50))
        self.stdout.write(self.style.SUCCESS("RESUMEN DE ASIGNACIÓN"))
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(f"✓ Asignados correctamente: {stats['assigned']}")
        self.stdout.write(f"⊗ Sin campaña activa: {stats['skipped_no_campaign']}")
        self.stdout.write(f"⊗ Conflictos de horario: {stats['skipped_conflict']}")
        self.stdout.write(f"⊗ Labs llenos: {stats['skipped_full']}")
        self.stdout.write(self.style.SUCCESS("=" * 50))

    def _has_schedule_conflict(self, student, lab_group):
        """Verifica si el estudiante tiene cruce de horario"""

        def overlap(s1, e1, s2, e2):
            return s1 < e2 and s2 < e1

        # Obtener todas las matrículas del estudiante
        enrollments = StudentEnrollment.objects.filter(
            student=student, status="ACTIVO"
        ).select_related("group")

        for enrollment in enrollments:
            # Verificar horarios de teoría
            if enrollment.group:
                schedules = Schedule.objects.filter(course_group=enrollment.group)
                for sch in schedules:
                    if sch.day_of_week == lab_group.day_of_week:
                        if overlap(
                            lab_group.start_time,
                            lab_group.end_time,
                            sch.start_time,
                            sch.end_time,
                        ):
                            return True

            # Verificar otros labs asignados
            if enrollment.lab_assignment:
                other_lab = enrollment.lab_assignment.lab_group
                if other_lab.day_of_week == lab_group.day_of_week:
                    if overlap(
                        lab_group.start_time,
                        lab_group.end_time,
                        other_lab.start_time,
                        other_lab.end_time,
                    ):
                        return True

        return False

    def _all_labs_full(self, campaign, labs):
        """Verifica si todos los labs están llenos"""
        for lab in labs:
            count = StudentPostulation.objects.filter(
                campaign=campaign, lab_group=lab
            ).count()
            if count < lab.capacity:
                return False
        return True
