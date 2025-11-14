from django.http import HttpResponseForbidden

class SecretariaPermissionService:
    @staticmethod
    def has_secretaria_access(user):
        return user.is_authenticated and user.user_role == 'SECRETARIA'
    
    @staticmethod
    def check_secretaria_access(user):
        if not SecretariaPermissionService.has_secretaria_access(user):
            raise PermissionError("No tienes permisos para acceder a esta sección")