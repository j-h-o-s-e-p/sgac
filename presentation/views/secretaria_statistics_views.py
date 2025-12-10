from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from presentation.views.mixins import SecretariaRequiredMixin 
from application.services.secretaria_services import SecretariaService

class SecretariaStatisticsView(LoginRequiredMixin, SecretariaRequiredMixin, TemplateView):
    template_name = 'secretaria/secretaria_statistics.html' 
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        semester_id = self.request.GET.get('semester')
        
        # Toda la lógica compleja está en el servicio
        stats_data = SecretariaService.get_statistics_context(semester_id)
        context.update(stats_data)
        
        return context