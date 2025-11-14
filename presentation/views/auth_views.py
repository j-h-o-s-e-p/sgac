from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required


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
                messages.error(request, 'Tu cuenta está inactiva. Contacta al administrador.')
        else:
            messages.error(request, 'Email o contraseña incorrectos.')
    
    return render(request, 'auth/login.html')


@login_required
def logout_view(request):
    """Vista de cierre de sesión"""
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente.')
    return redirect('presentation:login')