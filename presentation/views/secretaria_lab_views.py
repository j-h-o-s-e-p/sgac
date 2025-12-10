import json
from datetime import time
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import TemplateView, View
from django.http import JsonResponse

from .mixins import SecretariaRequiredMixin
from infrastructure.persistence.models import LaboratoryGroup, Classroom, CustomUser, ExternalProfessor, CourseGroup
from application.services.secretaria_services import SecretariaService

class LabManagementView(SecretariaRequiredMixin, TemplateView):
    template_name = 'secretaria/secretaria_lab_management.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        courses_with_lab = SecretariaService.get_courses_with_lab()
        courses_data = []
        
        for course in courses_with_lab:
            count = SecretariaService.get_course_enrollment_count(course.course_id)
            needed = SecretariaService.calculate_lab_groups_needed(count)
            existing = LaboratoryGroup.objects.filter(course=course)
            theory_ids = list(CourseGroup.objects.filter(course=course, professor__isnull=False).values_list('professor_id', flat=True))
            
            courses_data.append({
                'course': course,
                'enrollment_count': count,
                'labs_needed': needed,
                'existing_labs': existing,
                'has_all_labs': existing.count() >= needed,
                'theory_professors_ids': theory_ids
            })
        
        context['courses_data'] = courses_data
        context['classrooms'] = Classroom.objects.filter(is_active=True, classroom_type='LABORATORIO')
        context['professors'] = CustomUser.objects.filter(user_role='PROFESOR', is_active=True)
        context['external_professors'] = ExternalProfessor.objects.all()
        
        return context

class CreateLabGroupView(SecretariaRequiredMixin, View):
    def post(self, request):
        try:
            ext_data = None
            if request.POST.get('use_external_professor') == 'true':
                ext_data = {
                    'full_name': request.POST.get('external_prof_name'),
                    'email': request.POST.get('external_prof_email'), # Opcional si el form no lo envía
                    'phone': '', 
                    'specialization': ''
                }

            result = SecretariaService.create_lab_group(
                course_id=request.POST.get('course_id'),
                nomenclature=request.POST.get('nomenclature'),
                capacity=int(request.POST.get('capacity')),
                day=request.POST.get('day_of_week'),
                start=time.fromisoformat(request.POST.get('start_time')),
                end=time.fromisoformat(request.POST.get('end_time')),
                room_id=request.POST.get('room_id') or None,
                prof_id=request.POST.get('professor_id') or None,
                ext_prof_data=ext_data
            )
            
            if result['success']:
                messages.success(request, "Laboratorio creado exitosamente")
            else:
                for error in result['errors']: messages.error(request, error)
                    
        except Exception as e:
            messages.error(request, f"Error interno: {str(e)}")
        
        return redirect('presentation:secretaria_lab_management')

class DeleteLabGroupView(SecretariaRequiredMixin, View):
    def post(self, request, lab_id):
        lab = get_object_or_404(LaboratoryGroup, lab_id=lab_id)
        # Podrías agregar validación si tiene alumnos inscritos aquí
        lab.delete()
        messages.success(request, "Grupo de laboratorio eliminado.")
        return redirect('presentation:secretaria_lab_management')

class CheckScheduleConflictsView(View):
    """API JSON para verificar conflictos (usada por secretaria.js)"""
    def post(self, request):
        try:
            data = json.loads(request.body)
            conflicts = SecretariaService.check_schedule_conflicts(
                course_id=data.get('course_id'),
                day=data.get('day_of_week'),
                start=time.fromisoformat(data.get('start_time')),
                end=time.fromisoformat(data.get('end_time')),
                room_id=data.get('room_id'),
                exclude_lab_id=data.get('exclude_lab_id')
            )
            return JsonResponse(conflicts)
        except Exception as e:
            return JsonResponse({'has_conflict': True, 'messages': [f"Error de validación: {str(e)}"]}, status=400)

class GetAvailableClassroomsView(View):
    """API JSON para obtener salones disponibles"""
    def post(self, request):
        try:
            data = json.loads(request.body)
            classrooms = SecretariaService.get_available_classrooms(
                day=data.get('day_of_week'),
                start=time.fromisoformat(data.get('start_time')),
                end=time.fromisoformat(data.get('end_time'))
            )
            return JsonResponse({
                'success': True,
                'classrooms': [{'id': str(c.classroom_id), 'code': c.name, 'name': c.name, 'capacity': c.capacity} for c in classrooms]
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)