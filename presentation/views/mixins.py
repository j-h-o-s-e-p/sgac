from django.http import HttpResponseForbidden
from application.services.permissions import SecretariaPermissionService

class SecretariaRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        try:
            SecretariaPermissionService.check_secretaria_access(request.user)
            return super().dispatch(request, *args, **kwargs)
        except PermissionError:
            return HttpResponseForbidden("No tienes permisos para acceder a esta sección")