from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseNotAllowed

from infrastructure.persistence.models import Classroom, Course, CustomUser
from .mixins import SecretariaRequiredMixin

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
    fields = ['code', 'name', 'capacity', 'location', 'classroom_type', 'equipment']
    success_url = reverse_lazy('presentation:secretaria_classrooms') 

    def form_valid(self, form):
        messages.success(self.request, "Salón creado exitosamente.")
        return super().form_valid(form)

class ClassroomUpdateView(SecretariaRequiredMixin, UpdateView):
    model = Classroom
    template_name = 'secretaria/secretaria_classroom_form.html'
    fields = ['code', 'name', 'capacity', 'location', 'classroom_type', 'equipment']
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


class CourseScheduleView(SecretariaRequiredMixin, TemplateView):
    template_name = 'secretaria/secretaria_schedule.html'

class BulkUploadView(SecretariaRequiredMixin, TemplateView):
    template_name = 'secretaria/secretaria_upload.html'

def upload_cursos_view(request):
    if request.method == 'POST':
        # --- AQUÍ VA TU LÓGICA ---
        # 1. Obtener el archivo: request.FILES.get('file_cursos')
        # 2. Abrir con Pandas: pd.read_csv(...)
        # 3. Iterar y crear objetos (como en tu script)
        # 4. Añadir mensaje de éxito
        messages.success(request, "Archivo de cursos procesado (LÓGICA PENDIENTE).")
        return redirect('presentation:secretaria_upload')
    return HttpResponseNotAllowed(['POST'])

def upload_alumnos_view(request): 
    if request.method == 'POST':
        # --- AQUÍ VA TU LÓGICA ---
        # 1. Obtener archivos: request.FILES.getlist('file_alumnos')
        # 2. Iterar sobre cada archivo
        # 3. Abrir con Pandas
        # 4. Iterar y crear alumnos/matrículas (como en tu script)
        messages.success(request, "Archivos de alumnos procesados (LÓGICA PENDIENTE).")
        return redirect('presentation:secretaria_upload')
    return HttpResponseNotAllowed(['POST'])