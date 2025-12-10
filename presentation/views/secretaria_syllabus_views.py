from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin

from presentation.views.mixins import SecretariaRequiredMixin
from infrastructure.persistence.models import Syllabus
# Mantenemos el extractor aparte porque es lógica muy específica de PDF
from application.services.syllabus_extractor import SyllabusExtractor

class SyllabusListView(LoginRequiredMixin, SecretariaRequiredMixin, TemplateView):
    """Vista para listar sílabos subidos"""
    template_name = 'secretaria/secretaria_syllabus_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['syllabuses'] = Syllabus.objects.select_related(
            'course', 'course__semester'
        ).filter(syllabus_file__isnull=False).order_by('-loaded_at')
        return context

class ProcessSyllabusView(LoginRequiredMixin, SecretariaRequiredMixin, View):
    """Vista para procesar un sílabo individual"""
    
    def post(self, request, syllabus_id):
        syllabus = get_object_or_404(Syllabus, syllabus_id=syllabus_id)
        
        if not syllabus.syllabus_file:
            messages.error(request, "El sílabo no tiene archivo PDF asociado")
            return redirect('presentation:secretaria_syllabus_list')
        
        try:
            # Aquí usamos el Extractor directamente. 
            extractor = SyllabusExtractor(syllabus.syllabus_file.path)
            result = extractor.process_syllabus(syllabus)
            
            if result['success']:
                messages.success(request, f"Procesado: {result.get('units_created',0)} unds, {result.get('sessions_created',0)} sesiones.")
            else:
                messages.error(request, f"Error: {', '.join(result.get('errors', []))}")
                
        except Exception as e:
            messages.error(request, f"Error crítico: {str(e)}")
        
        return redirect('presentation:secretaria_syllabus_list')

class ReprocessAllSyllabusesView(LoginRequiredMixin, SecretariaRequiredMixin, View):
    """Vista para reprocesamiento masivo"""
    
    def post(self, request):
        syllabuses = Syllabus.objects.filter(syllabus_file__isnull=False)
        count = 0
        for syllabus in syllabuses:
            try:
                extractor = SyllabusExtractor(syllabus.syllabus_file.path)
                if extractor.process_syllabus(syllabus)['success']:
                    count += 1
            except Exception: pass
        
        messages.success(request, f"Procesamiento masivo completado: {count} sílabos actualizados.")
        return redirect('presentation:secretaria_syllabus_list')