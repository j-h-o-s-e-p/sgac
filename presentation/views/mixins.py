from django.shortcuts import redirect
from django.contrib import messages
from application.services.permissions import SecretariaPermissionService


class SecretariaRequiredMixin:
    """
    Mixin para asegurar que el usuario sea Secretaria.
    Si falla, redirige al login con un mensaje de error (Flash Message).
    """

    def dispatch(self, request, *args, **kwargs):
        # 1. Verificar si está logueado primero
        if not request.user.is_authenticated:
            messages.error(request, "Debes iniciar sesión para acceder a esta sección.")
            return redirect("presentation:login")

        try:
            # 2. Verificar rol usando el servicio
            SecretariaPermissionService.check_secretaria_access(request.user)
            return super().dispatch(request, *args, **kwargs)
        except PermissionError:
            # 3. Manejo amigable del error
            messages.error(
                request, "Acceso denegado: No tienes permisos de Secretaría."
            )
            # Redirigir al login
            return redirect("presentation:login")
