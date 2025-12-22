# Los roles que maneja mi sistema
ROLE_CHOICES = [
    ('ADMIN', 'Administrador'),
    ('PROFESOR', 'Profesor'),
    ('ALUMNO', 'Alumno'),
    ('SECRETARIA', 'Secretaría'),
]

# Estados posibles de la cuenta del usuario
USER_STATUS_CHOICES = [
    ('INACTIVO', 'Inactivo'), 
    ('ACTIVO', 'Activo'), 
    ('BLOQUEADO', 'Bloqueado'),
]