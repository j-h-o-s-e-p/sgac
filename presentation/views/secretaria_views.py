import json
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, HttpResponseNotAllowed
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView

from infrastructure.persistence.models import Classroom, CourseGroup, DAY_CHOICES
from .mixins import SecretariaRequiredMixin
from application.services.secretaria_services import SecretariaService

# --- Dashboard y CRUD Salones ---

class SecretariaDashboardView(SecretariaRequiredMixin, TemplateView):
    template_name = 'secretaria/secretaria_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(SecretariaService.get_dashboard_stats())
        return context

class ClassroomListView(SecretariaRequiredMixin, ListView):
    model = Classroom
    template_name = 'secretaria/secretaria_classroom_list.html'
    context_object_name = 'classroom_list' 
    queryset = Classroom.objects.filter(is_active=True).order_by('name')

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
    success_url = reverse_lazy('presentation:secretaria_classrooms')

    def get(self, request, *args, **kwargs):
        return redirect(self.success_url)

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Salón eliminado exitosamente.")
        return super().delete(request, *args, **kwargs)

# --- Programación de Horarios ---

class CourseScheduleView(SecretariaRequiredMixin, TemplateView):
    template_name = 'secretaria/secretaria_schedule.html' 

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['groups_data'] = SecretariaService.get_schedule_context()
        context['classrooms'] = Classroom.objects.filter(is_active=True).order_by('name')
        context['days_choices'] = DAY_CHOICES
        return context

def save_course_group_schedule(request):
    """API para guardar horarios (Recibe JSON desde secretaria.js)"""
    if request.method != 'POST': 
        return JsonResponse({'error': 'Método no permitido'}, status=405)
        
    try:
        data = json.loads(request.body)
        group_id = data.get('course_group_id')
        horarios = data.get('horarios', []) 

        if not group_id: 
            return JsonResponse({'error': 'ID de grupo faltante'}, status=400)

        SecretariaService.update_course_group_schedules(group_id, horarios)
        messages.success(request, "Horario actualizado correctamente.")
        return JsonResponse({'success': True})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# --- Carga Masiva ---

class BulkUploadView(SecretariaRequiredMixin, TemplateView):
    template_name = 'secretaria/secretaria_upload.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course_groups'] = CourseGroup.objects.select_related('course', 'professor').order_by('course__course_name')
        return context

def upload_students_to_group_view(request, group_id):
    if request.method != 'POST': 
        return HttpResponseNotAllowed(['POST'])
    
    csv_file = request.FILES.get('file_alumnos')
    if not csv_file or not csv_file.name.endswith('.csv'):
        messages.error(request, "Archivo inválido. Debe ser .csv")
        return redirect('presentation:secretaria_upload')

    result = SecretariaService.process_student_csv(group_id, csv_file)
    
    if result['success']:
        stats = result['stats']
        g = result['group']
        messages.success(request, f"Procesado: {stats['created']} nuevos, {stats['enrolled']} matriculados en {g.group_code}.")
    else:
        messages.error(request, f"Error: {result['error']}")

    return redirect('presentation:secretaria_upload')

# --- Reportes de Notas ---

class SecretariaGradeReportView(SecretariaRequiredMixin, TemplateView):
    template_name = 'secretaria/grade_report_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['groups'] = CourseGroup.objects.select_related('course', 'professor').order_by('course__course_code')
        return context

def download_grades_excel(request, group_id):
    try:
        wb, filename = SecretariaService.generate_grades_excel_workbook(group_id)
        
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename={filename}'
        wb.save(response)
        return response
    except Exception as e:
        messages.error(request, f"Error generando reporte: {e}")
        return redirect('presentation:secretaria_grade_report')