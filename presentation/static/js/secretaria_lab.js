/**
 * Lógica para Gestión de Laboratorios - Secretaría
 * Se encarga de modales, peticiones AJAX y manipulación del DOM.
 */

document.addEventListener('DOMContentLoaded', function() {
    initEnrollmentModal();
    initViewStudentsModal();
    initDeleteModal();
    initProfessorTypeToggles();
});

// 1. Manejo del Modal de Habilitar Inscripción
function initEnrollmentModal() {
    const modal = document.getElementById('enableEnrollmentModal');
    if (!modal) return;

    modal.addEventListener('show.bs.modal', function(event) {
        const button = event.relatedTarget;
        const courseId = button.getAttribute('data-course-id');
        // Obtenemos la URL base desde un atributo data en el botón o un input hidden global
        // Asumimos que la URL base se pasa en el atributo data-url-base del botón
        const urlBase = button.getAttribute('data-url-base'); 
        
        const form = document.getElementById('enableEnrollmentForm');
        // Reemplazamos el placeholder '0' o construimos la URL
        // Nota: Es mejor usar la URL generada por Django en el HTML y reemplazar el ID
        form.action = urlBase.replace('00000', courseId);
    });
}

// 2. Manejo del Modal de Ver Alumnos Inscritos
function initViewStudentsModal() {
    const modal = document.getElementById('enrolledStudentsModal');
    if (!modal) return;

    modal.addEventListener('show.bs.modal', function(event) {
        const button = event.relatedTarget;
        const labId = button.getAttribute('data-lab-id');
        const labName = button.getAttribute('data-lab-name');
        const urlFetch = button.getAttribute('data-url-fetch'); // URL dinámica desde Django
        
        document.getElementById('enrolledModalTitle').textContent = `Alumnos Inscritos - ${labName}`;
        const bodyContainer = document.getElementById('enrolledStudentsBody');
        
        // Loader
        bodyContainer.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Cargando...</span>
                </div>
                <p class="mt-2 text-muted">Cargando alumnos...</p>
            </div>
        `;

        // Petición Fetch
        fetch(urlFetch)
            .then(response => {
                if (!response.ok) throw new Error('Error en la respuesta del servidor');
                return response.json();
            })
            .then(data => {
                renderStudentsTable(data.students, bodyContainer);
            })
            .catch(error => {
                console.error('Error:', error);
                bodyContainer.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-triangle me-2"></i>
                        Error al cargar alumnos: ${error.message}
                    </div>
                `;
            });
    });
}

// Renderiza la tabla de estudiantes dentro del modal
function renderStudentsTable(students, container) {
    if (students.length === 0) {
        container.innerHTML = `
            <div class="text-center py-5">
                <i class="bi bi-inbox fs-1 text-muted"></i>
                <p class="mt-3 text-muted">No hay alumnos inscritos aún</p>
            </div>
        `;
        return;
    }

    let html = `
        <div class="table-responsive">
            <table class="table table-hover align-middle mb-0">
                <thead class="bg-light">
                    <tr>
                        <th>#</th>
                        <th>Alumno</th>
                        <th>Email</th>
                        <th>Inscrito</th>
                        <th>Estado</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    students.forEach(student => {
        const conflictBadge = student.has_conflict 
            ? '<span class="badge bg-danger ms-2">Cruce horario</span>' 
            : '';
            
        const statusBadge = student.has_conflict
            ? '<span class="badge bg-warning text-dark">Restringido</span>'
            : '<span class="badge bg-success">Libre</span>';

        html += `
            <tr>
                <td><strong>${student.order}</strong></td>
                <td>${student.full_name} ${conflictBadge}</td>
                <td><small class="text-muted">${student.email}</small></td>
                <td><small>${student.timestamp}</small></td>
                <td>${statusBadge}</td>
            </tr>
        `;
    });
    
    html += '</tbody></table></div>';
    container.innerHTML = html;
}

// 3. Manejo del Modal de Eliminar
function initDeleteModal() {
    const modal = document.getElementById('confirmDeleteModal');
    if (!modal) return;

    modal.addEventListener('show.bs.modal', function(event) {
        const button = event.relatedTarget;
        const urlDelete = button.getAttribute('data-url');
        const labName = button.getAttribute('data-name');

        document.getElementById('modalLabName').textContent = labName;
        document.getElementById('deleteForm').action = urlDelete;
    });
}

// 4. Toggle entre Profesor Interno y Externo (UI)
function initProfessorTypeToggles() {
    const forms = document.querySelectorAll('.lab-creation-form');
    
    forms.forEach(form => {
        const radios = form.querySelectorAll('.prof-type-radio');
        const internalSelect = form.querySelector('.internal-prof-select');
        const externalInput = form.querySelector('.external-prof-input');
        const useExternalHidden = form.querySelector('.use-external-hidden');

        radios.forEach(radio => {
            radio.addEventListener('change', (e) => {
                if (e.target.value === 'internal') {
                    internalSelect.disabled = false;
                    externalInput.disabled = true;
                    externalInput.value = '';
                    useExternalHidden.value = 'false';
                } else {
                    internalSelect.disabled = true;
                    internalSelect.value = '';
                    externalInput.disabled = false;
                    useExternalHidden.value = 'true';
                }
            });
        });
    });
}