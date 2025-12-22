import pdfplumber
import re
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional
from django.db import transaction


class SyllabusExtractor:
    """Servicio para extraer información del sílabo en PDF"""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.text = ""

    def extract_all_text(self) -> str:
        """Extrae todo el texto del PDF para búsquedas generales"""
        with pdfplumber.open(self.pdf_path) as pdf:
            self.text = ""
            for page in pdf.pages:
                self.text += page.extract_text() + "\n"
        return self.text

    def clean_text(self, text: str) -> str:
        """Limpia el texto de saltos de línea y espacios extra"""
        if not text:
            return ""
        # Reemplaza saltos de línea por espacios y elimina espacios dobles
        return " ".join(text.replace("\n", " ").split()).strip()

    def extract_credits(self) -> Optional[int]:
        pattern = r"Número de créditos:\s*(\d+)"
        match = re.search(pattern, self.text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    def extract_hours(self) -> Dict[str, Decimal]:
        hours = {
            "theory": Decimal("0.00"),
            "practice": Decimal("0.00"),
            "lab": Decimal("0.00"),
        }

        theory_match = re.search(r"Teóricas:\s*([\d.]+)", self.text, re.IGNORECASE)
        practice_match = re.search(r"Prácticas:\s*([\d.]+)", self.text, re.IGNORECASE)
        lab_match = re.search(r"Laboratorio:\s*([\d.]+)", self.text, re.IGNORECASE)

        if theory_match:
            hours["theory"] = Decimal(theory_match.group(1))
        if practice_match:
            hours["practice"] = Decimal(practice_match.group(1))
        if lab_match:
            hours["lab"] = Decimal(lab_match.group(1))

        return hours

    def extract_academic_schedule(self) -> List[Dict]:
        """
        Extrae el cronograma académico manejando filas multilinea.
        """
        sessions = []

        # Variables para mantener el estado mientras recorremos la tabla
        current_session = None

        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()

                for table in tables:
                    for row in table:
                        # Limpieza básica de la fila (None -> "")
                        clean_row = [
                            self.clean_text(cell) if cell else "" for cell in row
                        ]

                        # Saltamos filas vacías o muy cortas
                        if len(clean_row) < 2:
                            continue

                        col_semana = clean_row[0]
                        col_tema = clean_row[1]

                        # CASO 1: Es una NUEVA sesión
                        if col_semana.isdigit():
                            # Si ya estábamos procesando una sesión, la guardamos antes de empezar la nueva
                            if current_session:
                                sessions.append(current_session)

                            # Intentamos sacar el porcentaje
                            pct = Decimal("0.00")
                            for col in clean_row[3:]:  # Buscar en columnas finales
                                try:
                                    if col and any(c.isdigit() for c in col):
                                        val = col.replace("%", "").strip()
                                        pct = Decimal(val)
                                        break
                                except:
                                    continue

                            # Iniciamos la nueva sesión
                            current_session = {
                                "session_number": len(sessions) + 1,
                                "week_number": int(col_semana),
                                "topic": col_tema,
                                "accumulated_percentage": pct,
                            }

                        # CASO 2: Es CONTINUACIÓN de la sesión anterior
                        elif not col_semana and col_tema and current_session:
                            # Concatenamos el texto al tema existente
                            current_session["topic"] += " " + col_tema

        # No olvidar agregar la última sesión que quedó en memoria
        if current_session:
            sessions.append(current_session)

        # Post-procesamiento para limpiar espacios dobles generados por la unión
        for s in sessions:
            s["topic"] = " ".join(s["topic"].split())

            # Corrección específica para tu PDF
            s["topic"] = re.sub(r"^Tema \d+:\s*", "", s["topic"], flags=re.IGNORECASE)

        return sessions

    def extract_thematic_content(self) -> List[Dict]:
        """
        Extrae el contenido temático (Sección 5) basado en la estructura 'Tema X:'
        Esto es útil para llenar las UNIDADES con descripciones ricas.
        """
        units = []

        # 1. Identificar las Unidades
        unit_indices = []
        for match in re.finditer(
            r"(PRIMERA|SEGUNDA|TERCERA)\s+UNIDAD", self.text, re.IGNORECASE
        ):
            unit_indices.append({"name": match.group(0), "start": match.end()})

        # Si no encontró unidades con regex, asumimos una única unidad general
        if not unit_indices:
            unit_indices.append({"name": "UNIDAD ÚNICA", "start": 0})

        for i, u_data in enumerate(unit_indices):
            start = u_data["start"]
            end = (
                unit_indices[i + 1]["start"]
                if i + 1 < len(unit_indices)
                else len(self.text)
            )

            # Texto completo de la unidad
            unit_text = self.text[start:end]

            # Extraer Nombre del Capítulo
            chapter_match = re.search(r"Capítulo\s+[IVX]+:?\s*([^\n]+)", unit_text)
            chapter_name = (
                self.clean_text(chapter_match.group(1))
                if chapter_match
                else u_data["name"]
            )

            # Extraer Temas
            topics = []
            topic_matches = re.finditer(
                r"Tema\s+\d+:\s*(.+?)(?=(?:Tema\s+\d+:)|$|SEGUNDA|TERCERA)",
                unit_text,
                re.DOTALL,
            )

            for tm in topic_matches:
                # Limpiamos saltos de línea y espacios extra
                clean_topic = self.clean_text(tm.group(1))
                # Quitamos números de página o encabezados que se hayan colado
                clean_topic = re.sub(r"Página \d+/\d+", "", clean_topic).strip()
                if clean_topic:
                    topics.append(clean_topic)

            units.append(
                {"unit_number": i + 1, "unit_name": chapter_name, "topics": topics}
            )

        return units

    def extract_evaluation_schedule(self) -> List[Dict]:
        """
        Extrae el cronograma de evaluación (Sección 8.2)
        Retorna lista de evaluaciones con sus pesos
        """
        evaluations = []

        # Patrón para la tabla de evaluaciones
        pattern = r"(Primera|Segunda|Tercera)\s+Evaluación\s+Parcial\s+[\d-]+\s+(\d+)%\s+(\d+)%\s+(\d+)%"
        matches = re.findall(pattern, self.text, re.IGNORECASE)

        unit_map = {"Primera": 1, "Segunda": 2, "Tercera": 3}
        order = 1

        for match in matches:
            unit_text = match[0]
            unit = unit_map.get(unit_text, 1)
            exam_pct = Decimal(match[1])
            continua_pct = Decimal(match[2])

            # Crear evaluación continua
            evaluations.append(
                {
                    "name": f"EC{unit}",
                    "type": "CONTINUA",
                    "unit": unit,
                    "percentage": continua_pct,
                    "order": order,
                }
            )
            order += 1

            # Crear examen parcial
            evaluations.append(
                {
                    "name": f"EP{unit}",
                    "type": "EXAMEN",
                    "unit": unit,
                    "percentage": exam_pct,
                    "order": order,
                }
            )
            order += 1

        return evaluations

    def process_syllabus(self, syllabus_obj) -> Dict:
        """
        Procesa el sílabo completo y retorna toda la información extraída
        """
        from infrastructure.persistence.models import (
            Course,
            Syllabus,
            SyllabusUnit,
            SyllabusSession,
            Evaluation,
        )

        # Extraer texto
        self.extract_all_text()

        result = {
            "success": False,
            "credits": None,
            "hours": {},
            "units_created": 0,
            "sessions_created": 0,
            "evaluations_created": 0,
            "errors": [],
        }

        try:
            with transaction.atomic():
                SyllabusUnit.objects.filter(syllabus=syllabus_obj).delete()
                SyllabusSession.objects.filter(syllabus=syllabus_obj).delete()

                # 1. Extraer y actualizar créditos
                credits = self.extract_credits()
                if credits:
                    syllabus_obj.credits_extracted = credits
                    syllabus_obj.course.credits = credits
                    syllabus_obj.course.save(update_fields=["credits"])
                    result["credits"] = credits

                # 2. Extraer y actualizar horas
                hours = self.extract_hours()
                syllabus_obj.theory_hours = hours["theory"]
                syllabus_obj.practice_hours = hours["practice"]
                syllabus_obj.lab_hours = hours["lab"]
                result["hours"] = hours

                # 3. Crear unidades temáticas
                units_data = self.extract_thematic_content()
                for unit_data in units_data:
                    unit = SyllabusUnit.objects.create(
                        syllabus=syllabus_obj,
                        unit_number=unit_data["unit_number"],
                        unit_name=unit_data["unit_name"],
                        description=", ".join(unit_data["topics"]),
                    )
                    result["units_created"] += 1

                # 4. Crear sesiones del cronograma académico
                sessions_data = self.extract_academic_schedule()
                for session_data in sessions_data:
                    # Determinar a qué unidad pertenece
                    pct = session_data["accumulated_percentage"]
                    if pct <= 34:
                        unit_number = 1
                    elif pct <= 68:
                        unit_number = 2
                    else:
                        unit_number = 3

                    unit = SyllabusUnit.objects.filter(
                        syllabus=syllabus_obj, unit_number=unit_number
                    ).first()

                    SyllabusSession.objects.create(
                        syllabus=syllabus_obj,
                        session_number=session_data["session_number"],
                        unit=unit,
                        week_number=session_data["week_number"],
                        topic=session_data["topic"],
                        accumulated_percentage=session_data["accumulated_percentage"],
                    )
                    result["sessions_created"] += 1

                # 5. Crear evaluaciones (Solo si no están configuradas)
                if not syllabus_obj.evaluations_configured:
                    evaluations_data = self.extract_evaluation_schedule()
                    for eval_data in evaluations_data:
                        Evaluation.objects.create(
                            course=syllabus_obj.course,
                            name=eval_data["name"],
                            evaluation_type=eval_data["type"],
                            unit=eval_data["unit"],
                            percentage=eval_data["percentage"],
                            order=eval_data["order"],
                        )
                        result["evaluations_created"] += 1

                    syllabus_obj.evaluations_configured = True

                # Guardar cambios en el sílabo
                syllabus_obj.save()

                result["success"] = True

        except Exception as e:
            result["errors"].append(str(e))

        return result
