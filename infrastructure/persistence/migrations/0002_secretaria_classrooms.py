from django.db import migrations, models
import django.db.models.deletion
import uuid

def create_initial_classrooms(apps, schema_editor):
    """Crear classrooms iniciales basados en los rooms existentes"""
    Classroom = apps.get_model('persistence', 'Classroom')
    CourseGroup = apps.get_model('persistence', 'CourseGroup')
    LaboratoryGroup = apps.get_model('persistence', 'LaboratoryGroup')
    
    # Obtener todos los rooms únicos existentes
    course_rooms = CourseGroup.objects.values_list('room', flat=True).distinct()
    lab_rooms = LaboratoryGroup.objects.values_list('room', flat=True).distinct()
    all_rooms = set(course_rooms) | set(lab_rooms)
    
    # Crear classrooms para cada room único
    classroom_map = {}
    for room_name in all_rooms:
        if room_name:  # Solo si no está vacío
            classroom = Classroom.objects.create(
                code=room_name[:20],  # Asegurar que no exceda el límite
                name=f"Salón {room_name}",
                capacity=30,  # Capacidad por defecto
                location="Por definir",
                classroom_type='AULA',  # Tipo por defecto
                equipment="Equipamiento básico"
            )
            classroom_map[room_name] = classroom

def update_course_groups_with_classrooms(apps, schema_editor):
    """Actualizar CourseGroups con los nuevos classrooms"""
    Classroom = apps.get_model('persistence', 'Classroom')
    CourseGroup = apps.get_model('persistence', 'CourseGroup')
    
    for course_group in CourseGroup.objects.all():
        if course_group.room:
            try:
                classroom = Classroom.objects.get(code=course_group.room)
                course_group.classroom_new = classroom
                course_group.save()
            except Classroom.DoesNotExist:
                # Si no encuentra el classroom, crear uno
                classroom = Classroom.objects.create(
                    code=course_group.room[:20],
                    name=f"Salón {course_group.room}",
                    capacity=30,
                    location="Por definir",
                    classroom_type='AULA',
                    equipment="Equipamiento básico"
                )
                course_group.classroom_new = classroom
                course_group.save()

def update_lab_groups_with_classrooms(apps, schema_editor):
    """Actualizar LaboratoryGroups con los nuevos classrooms"""
    Classroom = apps.get_model('persistence', 'Classroom')
    LaboratoryGroup = apps.get_model('persistence', 'LaboratoryGroup')
    
    for lab_group in LaboratoryGroup.objects.all():
        if lab_group.room:
            try:
                classroom = Classroom.objects.get(code=lab_group.room)
                lab_group.classroom_new = classroom
                lab_group.save()
            except Classroom.DoesNotExist:
                # Si no encuentra el classroom, crear uno
                classroom = Classroom.objects.create(
                    code=lab_group.room[:20],
                    name=f"Laboratorio {lab_group.room}",
                    capacity=20,
                    location="Por definir",
                    classroom_type='LABORATORIO',
                    equipment="Equipos de laboratorio"
                )
                lab_group.classroom_new = classroom
                lab_group.save()

class Migration(migrations.Migration):

    dependencies = [
        ('persistence', '0001_initial'),
    ]

    operations = [
        # 1. Crear el modelo Classroom
        migrations.CreateModel(
            name='Classroom',
            fields=[
                ('classroom_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('code', models.CharField(max_length=20, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('capacity', models.IntegerField()),
                ('location', models.CharField(max_length=200)),
                ('classroom_type', models.CharField(choices=[('AULA', 'Aula'), ('LABORATORIO', 'Laboratorio'), ('AUDITORIO', 'Auditorio')], max_length=20)),
                ('equipment', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'classrooms',
                'verbose_name': 'Salón',
                'verbose_name_plural': 'Salones',
            },
        ),
        
        # 2. Agregar nuevos campos ForeignKey (temporal)
        migrations.AddField(
            model_name='coursegroup',
            name='classroom_new',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='course_groups', to='persistence.classroom'),
        ),
        migrations.AddField(
            model_name='laboratorygroup',
            name='classroom_new',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='lab_groups', to='persistence.classroom'),
        ),
        
        # 3. Ejecutar las funciones de datos
        migrations.RunPython(create_initial_classrooms),
        migrations.RunPython(update_course_groups_with_classrooms),
        migrations.RunPython(update_lab_groups_with_classrooms),
        
        # 4. Eliminar los campos antiguos
        migrations.RemoveField(
            model_name='coursegroup',
            name='room',
        ),
        migrations.RemoveField(
            model_name='laboratorygroup',
            name='room',
        ),
        
        # 5. Renombrar los nuevos campos
        migrations.RenameField(
            model_name='coursegroup',
            old_name='classroom_new',
            new_name='room',
        ),
        migrations.RenameField(
            model_name='laboratorygroup',
            old_name='classroom_new',
            new_name='room',
        ),
    ]