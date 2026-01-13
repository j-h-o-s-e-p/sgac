from django.utils.deprecation import MiddlewareMixin


class NoCacheMiddleware(MiddlewareMixin):
    """
    Middleware para agregar cabeceras que deshabilitan la caché del navegador
    en páginas donde el usuario está autenticado.
    Esto evita que al dar 'Atrás' después de un logout se vea la sesión anterior.
    """

    def process_response(self, request, response):
        if request.user.is_authenticated:
            response["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"
        return response
