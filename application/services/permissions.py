class SecretariaPermissionService:
    @staticmethod
    def has_secretaria_access(user):
        # Verifica si está logueado y es secretaria
        return user.is_authenticated and user.user_role == 'SECRETARIA'
    
    @staticmethod
    def check_secretaria_access(user):
        if not SecretariaPermissionService.has_secretaria_access(user):
            # Lanzamos error puro de Python. El Mixin se encargará de traducirlo a HTTP.
            raise PermissionError("No tienes permisos para acceder a esta sección")