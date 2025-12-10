import json
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

def login_view(request):
    """Vista de inicio de sesión"""
    
    # Si ya está autenticado, redirigir según su rol
    if request.user.is_authenticated:
        if request.user.user_role == 'ALUMNO':
            return redirect('presentation:student_dashboard')
        elif request.user.user_role == 'PROFESOR':
            return redirect('presentation:professor_dashboard')
        elif request.user.user_role == 'SECRETARIA':
            return redirect('presentation:secretaria_dashboard')
        else:
            return redirect('admin:index')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Autenticar usuario
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            if user.account_status == 'ACTIVO':
                login(request, user)
                
                # Redirigir según el rol
                if user.user_role == 'ALUMNO':
                    return redirect('presentation:student_dashboard')
                elif user.user_role == 'PROFESOR':
                    return redirect('presentation:professor_dashboard')
                elif user.user_role == 'SECRETARIA':
                    return redirect('presentation:secretaria_dashboard')
                else:
                    return redirect('admin:index')
            else:
                messages.warning(request, 'Tu cuenta está inactiva. Contacta al administrador.')
        else:
            messages.error(request, 'Email o contraseña incorrectos.')
    
    return render(request, 'auth/login.html')


@login_required
def logout_view(request):
    """Vista de cierre de sesión"""
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente.')
    return redirect('presentation:login')


@login_required
@require_http_methods(["POST"])
def change_password_view(request):
    """
    Procesa el cambio de contraseña vía AJAX.
    Retorna JSON: {'success': True/False, 'message': '...'}
    """
    try:
        # Intentamos leer los datos como JSON (para la petición AJAX)
        data = json.loads(request.body)
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        # 1. Verificar contraseña antigua
        if not request.user.check_password(old_password):
            return JsonResponse({
                'success': False, 
                'error_type': 'old_password',
                'message': 'La contraseña actual no es correcta.'
            }, status=400)

        # 2. Verificar que las nuevas coincidan
        if new_password != confirm_password:
            return JsonResponse({
                'success': False, 
                'error_type': 'match',
                'message': 'Las nuevas contraseñas no coinciden.'
            }, status=400)
            
        # 3. Verificar que la nueva no sea igual a la actual
        if old_password == new_password:
             return JsonResponse({
                'success': False, 
                'error_type': 'same_password',
                'message': 'La nueva contraseña no puede ser igual a la actual.'
            }, status=400)

        # 4. Validar longitud
        if len(new_password) < 6:
            return JsonResponse({
                'success': False, 
                'error_type': 'length',
                'message': 'La contraseña debe tener al menos 6 caracteres.'
            }, status=400)

        # 5. Todo OK: Cambiar y actualizar sesión
        request.user.set_password(new_password)
        request.user.save()
        update_session_auth_hash(request, request.user) # Mantiene la sesión viva
        
        return JsonResponse({'success': True, 'message': 'Contraseña actualizada correctamente.'})

    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error del servidor: {str(e)}'}, status=500)