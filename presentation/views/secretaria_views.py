import json
import csv
import io
from django.db import transaction
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseNotAllowed, JsonResponse
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password
from django.utils import timezone 

# --- Modelos de Infrastructure ---
from infrastructure.persistence.models import (
    Classroom, 
    Course, 
    CustomUser,
    CourseGroup,  
    Schedule,
    StudentEnrollment 
)

from infrastructure.persistence.models import DAY_CHOICES 

# --- Mixins ---
from .mixins import SecretariaRequiredMixin

# --- Vistas de Dashboard y Salones ---

class SecretariaDashboardView(SecretariaRequiredMixin, TemplateView):
    template_name = 'secretaria/secretaria_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['classrooms_count'] = Classroom.objects.filter(is_active=True).count()
        context['courses_count'] = Course.objects.count()
        context['professors_count'] = CustomUser.objects.filter(user_role='PROFESOR', is_active=True).count()
        context['students_count'] = CustomUser.objects.filter(user_role='ALUMNO', is_active=True).count()
        return context

class ClassroomListView(SecretariaRequiredMixin, ListView):
    model = Classroom
    template_name = 'secretaria/secretaria_classroom_list.html'
    context_object_name = 'classroom_list' 
    queryset = Classroom.objects.filter(is_active=True) 

class ClassroomCreateView(SecretariaRequiredMixin, CreateView):
    model = Classroom
    template_name = 'secretaria/secretaria_classroom_form.html'
    fields = ['name', 'capacity', 'location', 'classroom_type'] 
    success_url = reverse_lazy('presentation:secretaria_classrooms') 

    def form_valid(self, form):
        messages.success(self.request, "Salón creado exitosamente.")
        return super().form_valid(form)

class ClassroomUpdateView(SecretariaRequiredMixin, UpdateView):
    model = Classroom
    template_name = 'secretaria/secretaria_classroom_form.html'
    fields = ['name', 'capacity', 'location', 'classroom_type']
    success_url = reverse_lazy('presentation:secretaria_classrooms') 

    def form_valid(self, form):
        messages.success(self.request, "Salón actualizado exitosamente.")
        return super().form_valid(form)

class ClassroomDeleteView(SecretariaRequiredMixin, DeleteView):
    model = Classroom
    template_name = 'secretaria/secretaria_confirm_delete.html' 
    success_url = reverse_lazy('presentation:secretaria_classrooms')

    def form_valid(self, form):
        messages.success(self.request, "Salón eliminado exitosamente.")
        return super().form_valid(form)

# --- Vista de Programación ---
class CourseScheduleView(SecretariaRequiredMixin, TemplateView):
    template_name = 'secretaria/secretaria_schedule.html' 

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        groups_qs = CourseGroup.objects.select_related(
            'course', 
            'professor'
        ).prefetch_related(
            'schedules', 
            'schedules__room'
        ).all()
        
        groups_data_list = []
        for group in groups_qs:
            schedules_json_data = [
                {
                    'day_of_week': schedule.day_of_week,
                    'start_time': schedule.start_time.strftime('%H:%M'),
                    'end_time': schedule.end_time.strftime('%H:%M'),
                    'room_id': schedule.room.classroom_id if schedule.room else None,
                }
                for schedule in group.schedules.all()
            ]
            
            groups_data_list.append({
                'group_object': group, 
                'schedules_json_data': schedules_json_data, 
            })

        context['groups_data'] = groups_data_list
        context['classrooms'] = Classroom.objects.filter(is_active=True).order_by('name')
        context['days_choices'] = DAY_CHOICES
        
        return context

# --- Vistas de Carga Masiva ---

class BulkUploadView(SecretariaRequiredMixin, TemplateView):
    """
    Carga la lista de grupos de cursos para mostrarlos en el template.
    """
    template_name = 'secretaria/secretaria_upload.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Carga todos los grupos, optimizando con select_related
        context['course_groups'] = CourseGroup.objects.select_related(
            'course', 
            'professor'
        ).order_by('course__course_name', 'group_code')
        return context


def _get_email_and_names(full_name_csv, cui):
    """
    Función helper para generar el email y formatear los nombres desde el CSV.
    """
    try:
        full_name_csv = full_name_csv.strip().replace('"', '')
        parts = full_name_csv.split(',') 
        if len(parts) < 2:
            return "NombreCsvMalformado", "", f"error_{cui}@unsa.edu.pe"

        last_names_part = parts[0].strip() 
        first_names_part = parts[1].strip() 
        
        last_names_list = last_names_part.split('/') 
        
        first_name = " ".join([n.capitalize() for n in first_names_part.split() if n])
        last_paterno = last_names_list[0].capitalize() if last_names_list else ""
        last_materno = last_names_list[1].capitalize() if len(last_names_list) > 1 else ""
        last_name = f"{last_paterno} {last_materno}".strip()

        if not first_name or not last_paterno:
                return "NombreCsvIncompleto", "", f"error_{cui}@unsa.edu.pe"

        # --- Generar Email ---
        initial = first_name[0].lower() 
        paterno_email = last_names_list[0].lower() 
        
        email_prefix = f"{initial}{paterno_email}" 
        email = f"{email_prefix}@unsa.edu.pe" 

        # Verificar colisión
        if CustomUser.objects.filter(email=email).exclude(username=cui).exists():
            if len(last_names_list) > 1:
                # Intenta con materno
                materno_email = last_names_list[1].lower()
                email_prefix = f"{initial}{paterno_email}{materno_email}"
                email = f"{email_prefix}@unsa.edu.pe"
            else:
                # Si sigue colisionando y no hay materno, usar CUI
                email = f"{email_prefix}{cui}@unsa.edu.pe" 
        
        # Chequeo final de colisión
        if CustomUser.objects.filter(email=email).exclude(username=cui).exists():
                email = f"{initial}{paterno_email}{cui}@unsa.edu.pe" # Email más único

        return first_name, last_name, email

    except Exception:
        return "ErrorParsing", "ErrorParsing", f"error_{cui}@unsa.edu.pe"

def upload_students_to_group_view(request, group_id):
    """
    NUEVA VISTA: Procesa el CSV de alumnos para un grupo específico.
    """
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    
    group = get_object_or_404(CourseGroup, group_id=group_id)
    csv_file = request.FILES.get('file_alumnos')

    if not csv_file:
        messages.error(request, "No se seleccionó ningún archivo.")
        return redirect('presentation:secretaria_upload')
    
    if not csv_file.name.endswith('.csv'):
        messages.error(request, "El archivo debe tener formato .csv")
        return redirect('presentation:secretaria_upload')

    student_cuis_in_csv = set()
    students_created_count = 0
    students_enrolled_count = 0
    
    try:
        # Decodificar el archivo
        data = csv_file.read().decode('utf-8')
        io_string = io.StringIO(data)
        reader = csv.reader(io_string)
        # Saltar la cabecera
        next(reader, None) 

        with transaction.atomic():
            # 1. Obtener alumnos ya matriculados en ESTE grupo
            current_enrollments = StudentEnrollment.objects.filter(group=group)
            existing_student_ids_in_group = set(
                current_enrollments.values_list('student__username', flat=True)
            )

            for row in reader:
                if not row or not row[1] or not row[2]:
                    continue 
                
                cui = row[1].strip()
                full_name_csv = row[2].strip().upper() 
                
                if not cui.isdigit():
                    continue 
                student_cuis_in_csv.add(cui)
                student = None
                
                try:
                    # 2. Verificar si el usuario alumno ya existe por CUI (user_id)
                    student = CustomUser.objects.get(username=cui)

                    if not student.is_active or student.account_status != 'ACTIVO':
                        student.is_active = True
                        student.account_status = 'ACTIVO'
                        student.save(update_fields=['is_active', 'account_status'])
                    
                    # 3. Actualizar nombres si difieren
                    if student.first_name.upper() not in full_name_csv or student.last_name.upper() not in full_name_csv:
                        first_name, last_name, email = _get_email_and_names(full_name_csv, cui)
                        student.first_name = first_name
                        student.last_name = last_name
                        student.save()

                except CustomUser.DoesNotExist:
                    first_name, last_name, email = _get_email_and_names(full_name_csv, cui)
                    
                    student = CustomUser.objects.create(
                        username=cui, 
                        password=make_password(cui), 
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        user_role='ALUMNO',
                        is_active=True,
                        account_status='ACTIVO',
                        is_staff=False,
                        is_superuser=False
                    )
                    students_created_count += 1
                
                # 4. Matricular al alumno si no lo está ya
                if cui not in existing_student_ids_in_group:
                    StudentEnrollment.objects.create(
                        student=student, 
                        group=group,
                        course=group.course
                    )
                    students_enrolled_count += 1
            
            # 5. Lógica de Sincronización 
            # Desmatricular alumnos que estaban en el grupo pero ya no están en el CSV
            cuis_to_remove = existing_student_ids_in_group - student_cuis_in_csv
            removed_count = 0
            if cuis_to_remove:

                enrollments_to_delete = StudentEnrollment.objects.filter(
                    group=group,
                    student__username__in=cuis_to_remove
                )
                removed_count = enrollments_to_delete.count()
                enrollments_to_delete.delete()
        
        # 6. Marcar el grupo como con alumnos cargados y actualiza la capacidad
        new_capacity = len(student_cuis_in_csv)
        group.students_loaded = True
        group.last_student_upload_at = timezone.now()
        group.capacity = new_capacity
        group.save(update_fields=['students_loaded', 'last_student_upload_at', 'capacity'])

        messages.success(request, f"Carga exitosa para {group.course.course_name} - G{group.group_code}: "
                                 f"{students_created_count} alumnos creados, "
                                 f"{students_enrolled_count} nuevos matriculados, "
                                 f"{removed_count} desmatriculados."
                                 f" Capacidad actualizada a {new_capacity}.")

    except Exception as e:
        messages.error(request, f"Error al procesar el archivo para el grupo {group.group_code}: {str(e)}")

    return redirect('presentation:secretaria_upload')


# --- API VIEW  ---
@csrf_exempt 
def save_course_group_schedule(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
        
    try:
        data = json.loads(request.body)
        course_group_id = data.get('course_group_id')
        horarios = data.get('horarios', []) 

        if not course_group_id:
            return JsonResponse({'success': False, 'error': 'ID de grupo faltante'}, status=400)

        group = get_object_or_404(CourseGroup, group_id=course_group_id)

        with transaction.atomic():
            dias_a_actualizar = set()
            
            for horario in horarios:
                if not horario.get('day') or not horario.get('start_time') or not horario.get('end_time') or not horario.get('room_id'):
                    raise ValueError(f"Entrada de horario incompleta: {horario}")
                
                dias_a_actualizar.add(horario['day'])
            
            if dias_a_actualizar:
                group.schedules.filter(day_of_week__in=dias_a_actualizar).delete()
            
            for horario in horarios:
                Schedule.objects.create(
                    course_group=group,
                    room_id=horario['room_id'],
                    day_of_week=horario['day'],
                    start_time=horario['start_time'],
                    end_time=horario['end_time']
                )

        return JsonResponse({'success': True})
    
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)