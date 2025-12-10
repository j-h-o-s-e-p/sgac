document.addEventListener('DOMContentLoaded', function() {
    console.log('Módulo de Secretaría cargado.');

    // ==========================================================
    // 1. ELIMINACIÓN DE REGISTROS (MODAL GENÉRICO)
    // ==========================================================
    // Funciona para Salones, y futuros elementos con la clase .btn-delete-classroom
    const deleteModal = document.getElementById('confirmDeleteModal');
    if (deleteModal) {
        deleteModal.addEventListener('show.bs.modal', function (event) {
            // Botón que disparó el modal
            const button = event.relatedTarget;
            
            // Extraer info de los atributos data-*
            const deleteUrl = button.getAttribute('data-url');
            const name = button.getAttribute('data-name');
            
            // Actualizar el formulario del modal
            const deleteForm = deleteModal.querySelector('#deleteForm');
            if(deleteForm) deleteForm.action = deleteUrl;
            
            // Actualizar el texto del modal
            const nameEl = deleteModal.querySelector('#modalClassroomName');
            if(nameEl) nameEl.textContent = name;
        });
    }

    // ==========================================================
    // 2. AUTO-ESTILIZADO DE FORMULARIOS DJANGO
    // ==========================================================
    // Busca formularios específicos y añade clases Bootstrap a los inputs crudos de Django
    const classroomForm = document.getElementById('classroomForm');
    
    if (classroomForm) {
        const inputs = classroomForm.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            if (input.type !== 'checkbox' && input.type !== 'radio' && input.type !== 'hidden') {
                if (input.tagName === 'SELECT') {
                    input.classList.add('form-select');
                } else {
                    input.classList.add('form-control');
                }
            }
        });
    }

    // ==========================================================
    // 3. GESTIÓN DE LABORATORIOS (Lógica Dinámica)
    // ==========================================================
    
    // A. Inicializar valores al abrir el formulario (Botón "Crear Nuevo Grupo")
    const labToggleButtons = document.querySelectorAll('.btn-toggle-lab-form');
    labToggleButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const courseId = this.getAttribute('data-course-id');
            const enrollment = parseInt(this.getAttribute('data-enrollment'));
            const needed = parseInt(this.getAttribute('data-needed'));
            
            // Calcular capacidad sugerida
            const suggested = Math.ceil(enrollment / needed);
            
            // Buscar el formulario correspondiente a este curso
            const form = document.getElementById(`form-${courseId}`);
            if (form) {
                const capacityInput = form.querySelector('.capacity-input');
                const suggestedSpan = form.querySelector('.suggested-capacity');
                
                if (capacityInput && !capacityInput.value) capacityInput.value = suggested;
                if (suggestedSpan) suggestedSpan.textContent = suggested;
            }
        });
    });

    // B. Toggle Profesor Interno vs Externo
    const profTypeRadios = document.querySelectorAll('.prof-type-radio');
    profTypeRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            // Buscamos el formulario padre para no afectar a otros cursos
            const form = this.closest('form');
            const targetType = this.value; // 'internal' o 'external'
            
            const internalSelect = form.querySelector('.internal-prof-select');
            const externalInput = form.querySelector('.external-prof-input');
            const hiddenInput = form.querySelector('.use-external-hidden');

            if (targetType === 'internal') {
                internalSelect.disabled = false;
                externalInput.disabled = true;
                externalInput.value = '';
                hiddenInput.value = 'false';
            } else {
                internalSelect.disabled = true;
                internalSelect.value = '';
                externalInput.disabled = false;
                hiddenInput.value = 'true';
            }
        });
    });

    // C. Verificación de Conflictos (AJAX)
    // Delegación de eventos para inputs de horario (.lab-schedule-input)
    document.body.addEventListener('change', function(e) {
        if (e.target.classList.contains('lab-schedule-input')) {
            const form = e.target.closest('form');
            checkLabConflicts(form);
        }
    });

    function checkLabConflicts(form) {
        if (!form) return;

        const courseId = form.getAttribute('data-course-id');
        const day = form.querySelector('[name="day_of_week"]').value;
        const startTime = form.querySelector('[name="start_time"]').value;
        const endTime = form.querySelector('[name="end_time"]').value;
        const roomId = form.querySelector('[name="room_id"]').value;
        
        // Solo consultar si tenemos datos mínimos
        if (!day || !startTime || !endTime) return;

        const urlInput = document.getElementById('url-check-conflicts');
        if (!urlInput) return;
        const url = urlInput.value;

        // Recuperar CSRF Token (reutilizamos la función del main.js si es global, o la leemos del input)
        const csrfToken = form.querySelector('[name="csrfmiddlewaretoken"]').value;

        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                course_id: courseId,
                day_of_week: day,
                start_time: startTime,
                end_time: endTime,
                room_id: roomId
            })
        })
        .then(response => response.json())
        .then(data => {
            const alertBox = form.querySelector('.conflict-alert');
            const messageBox = form.querySelector('.conflict-message');
            const iconBox = form.querySelector('.alert-icon');
            
            alertBox.classList.remove('d-none');
            
            if (data.has_conflict) {
                alertBox.classList.remove('alert-success', 'alert-info');
                alertBox.classList.add('alert-danger');
                iconBox.classList.replace('bi-check-circle-fill', 'bi-exclamation-triangle-fill');
                messageBox.textContent = `Conflicto: ${data.messages.join(', ')}`;
            } else {
                alertBox.classList.remove('alert-danger', 'alert-info');
                alertBox.classList.add('alert-success');
                iconBox.classList.replace('bi-exclamation-triangle-fill', 'bi-check-circle-fill');
                messageBox.textContent = 'Horario disponible y sin conflictos.';
            }
        })
        .catch(err => console.error('Error verificando conflictos:', err));
    }

    // D. Modal de Eliminación de Labs (Reutiliza la lógica genérica del paso 1, 
    // pero aseguramos que funcione para el botón .btn-delete-lab)
    const deleteLabBtns = document.querySelectorAll('.btn-delete-lab');
    deleteLabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const modal = document.getElementById('confirmDeleteModal');
            if(modal) {
                const url = this.getAttribute('data-url');
                const name = this.getAttribute('data-name');
                
                modal.querySelector('#deleteForm').action = url;
                modal.querySelector('#modalLabName').textContent = name;
            }
        });
    });

    // ==========================================================
    // 4. PROGRAMACIÓN DE CURSOS (HORARIOS)
    // ==========================================================
    
    // Variables para el módulo de horarios
    const scheduleModalEl = document.getElementById('scheduleModal');
    let scheduleModalInstance = null;
    
    if (scheduleModalEl) {
        scheduleModalInstance = new bootstrap.Modal(scheduleModalEl);
        
        // Elementos DOM
        const entriesContainer = document.getElementById('schedule-entries-container');
        const addBtn = document.getElementById('add-schedule-entry');
        const saveBtn = document.getElementById('btn-save-schedule');
        const errorMsg = document.getElementById('modal-error-message');
        const template = document.getElementById('schedule-entry-template');

        // Función para crear una fila
        const createRow = (data = null) => {
            const clone = template.content.cloneNode(true);
            const row = clone.querySelector('.schedule-entry');
            
            // Referencias a inputs
            const daySelect = row.querySelector('.field-day');
            const roomSelect = row.querySelector('.field-room');
            const startInput = row.querySelector('.field-start');
            const endInput = row.querySelector('.field-end');
            const removeBtn = row.querySelector('.btn-remove-entry');
            
            // Precargar datos si existen
            if (data) {
                daySelect.value = data.day_of_week;
                roomSelect.value = data.room_id || ""; // Manejar si room es null
                startInput.value = data.start_time;
                endInput.value = data.end_time;
            }
            
            // Evento eliminar
            removeBtn.addEventListener('click', () => row.remove());
            
            entriesContainer.appendChild(row);
        };

        // A. Abrir Modal y Cargar Datos
        document.querySelectorAll('.btn-edit-schedule').forEach(btn => {
            btn.addEventListener('click', function() {
                const groupId = this.getAttribute('data-group-id');
                const groupName = this.getAttribute('data-group-name');
                
                // Limpiar modal
                entriesContainer.innerHTML = '';
                errorMsg.classList.add('d-none');
                document.getElementById('modal_course_group_id').value = groupId;
                document.getElementById('modal-group-name-title').textContent = groupName;
                
                // Cargar horarios existentes
                // Nota: Los datos vienen como string JSON en el atributo data-schedules
                // Django template filter |safe asegura que las comillas estén bien, 
                // pero a veces el navegador escapa las comillas.
                // Es más seguro leerlo como objeto si se pasó vía json_script, 
                // pero en este refactor optimizado lo pusimos directo en data-attribute para simplificar el DOM.
                // Si el JSON es complejo, usar json_script es mejor.
                
                let schedules = [];
                try {
                    // Intentamos parsear. Si falla, asumimos vacío.
                    // Nota: En el HTML usamos data-schedules='{{ ...|safe }}'.
                    // Asegúrate de que tu vista envíe JSON válido.
                    const rawJson = this.getAttribute('data-schedules');
                    if (rawJson) schedules = JSON.parse(rawJson);
                } catch (e) {
                    console.error("Error parseando horarios", e);
                }
                
                if (schedules && schedules.length > 0) {
                    schedules.forEach(s => createRow(s));
                } else {
                    createRow(); // Fila vacía por defecto
                }
                
                scheduleModalInstance.show();
            });
        });

        // B. Botón Añadir Fila
        if(addBtn) {
            addBtn.addEventListener('click', () => createRow());
        }

        // C. Guardar Cambios (AJAX)
        if(saveBtn) {
            saveBtn.addEventListener('click', function() {
                errorMsg.classList.add('d-none');
                
                const rows = entriesContainer.querySelectorAll('.schedule-entry');
                const horarios = [];
                let hasError = false;
                
                rows.forEach(row => {
                    const day = row.querySelector('.field-day').value;
                    const room = row.querySelector('.field-room').value;
                    const start = row.querySelector('.field-start').value;
                    const end = row.querySelector('.field-end').value;
                    
                    if (!day || !room || !start || !end) {
                        hasError = true;
                        return;
                    }
                    
                    if (start >= end) {
                        hasError = true;
                        alert('La hora de inicio debe ser menor a la hora de fin en una de las filas.');
                        return;
                    }
                    
                    horarios.push({
                        day: day,
                        room_id: room,
                        start_time: start,
                        end_time: end
                    });
                });
                
                if (hasError) {
                    errorMsg.textContent = "Por favor completa todos los campos correctamente.";
                    errorMsg.classList.remove('d-none');
                    return;
                }

                // Enviar datos
                const url = document.getElementById('api-save-schedule-url').value;
                const groupId = document.getElementById('modal_course_group_id').value;
                
                // Necesitamos el token CSRF. Lo buscamos en cualquier form de la página o cookie
                const csrfToken = getCookie('csrftoken'); // Usamos la función helper global

                fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({
                        course_group_id: groupId,
                        horarios: horarios
                    })
                })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        location.reload(); // Recargar para ver cambios
                    } else {
                        errorMsg.textContent = data.error || "Error al guardar.";
                        errorMsg.classList.remove('d-none');
                    }
                })
                .catch(err => {
                    console.error(err);
                    errorMsg.textContent = "Error de conexión.";
                    errorMsg.classList.remove('d-none');
                });
            });
        }
    }

    // ==========================================================
    // 5. BUSCADOR DE REPORTES DE NOTAS
    // ==========================================================
    const searchInput = document.getElementById('gradeReportSearch');
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            const filter = this.value.toLowerCase();
            const rows = document.querySelectorAll('#groupsTable .group-row');
            let hasVisible = false;

            rows.forEach(row => {
                const text = row.innerText.toLowerCase();
                if (text.includes(filter)) {
                    row.style.display = '';
                    hasVisible = true;
                } else {
                    row.style.display = 'none';
                }
            });

            // Mostrar mensaje si no hay resultados
            const noResMsg = document.getElementById('noResultsMessage');
            if (noResMsg) {
                if (!hasVisible) {
                    noResMsg.classList.remove('d-none');
                    document.getElementById('groupsTable').classList.add('d-none');
                } else {
                    noResMsg.classList.add('d-none');
                    document.getElementById('groupsTable').classList.remove('d-none');
                }
            }
        });
    }

    // ==========================================================
    // 6. GRÁFICOS DASHBOARD SECRETARÍA 
    // ==========================================================
    
    const initCharts = () => {
        const saturationEl = document.getElementById('data-saturation');
        
        if (saturationEl && typeof Chart !== 'undefined') {
            try {
                // Helper para parsear datos de Django de forma segura
                const parseDjangoData = (elementId) => {
                    const el = document.getElementById(elementId);
                    if (!el) return null;
                    let content = JSON.parse(el.textContent);
                    if (typeof content === 'string') content = JSON.parse(content);
                    return content;
                };

                const saturationData = parseDjangoData('data-saturation');
                const courseData = parseDjangoData('data-courses');
                const professorsData = parseDjangoData('data-professors');

                // Configuración Global
                Chart.defaults.font.family = "'Segoe UI', sans-serif";
                Chart.defaults.color = '#64748b';
                Chart.defaults.maintainAspectRatio = false;

                // --------------------------------------------------
                // GRÁFICO 1: SATURACIÓN (Estado de Grupos)
                // --------------------------------------------------
                const satCanvas = document.getElementById('saturationChart');
                if (satCanvas) {
                    new Chart(satCanvas, {
                        type: 'doughnut',
                        data: {
                            // Etiquetas explicativas en lugar de genéricas
                            labels: saturationData.labels || ['Crítico (>90%)', 'Óptimo (50-90%)', 'Baja Demanda (<50%)'], 
                            datasets: [{
                                data: saturationData.data || [],
                                backgroundColor: [
                                    '#ef4444', // Rojo (Crítico/Lleno)
                                    '#10b981', // Verde (Bien/Normal)
                                    '#f59e0b'  // Amarillo (Vacío/Baja demanda)
                                ],
                                borderWidth: 2,
                                borderColor: '#ffffff',
                                hoverOffset: 10
                            }]
                        },
                        options: {
                            plugins: {
                                legend: { 
                                    position: 'right', 
                                    labels: { usePointStyle: true, boxWidth: 8 } 
                                },
                                tooltip: {
                                    callbacks: {
                                        label: function(context) {
                                            // Calcula el porcentaje del total para dar contexto
                                            let value = context.raw;
                                            let total = context.chart._metasets[context.datasetIndex].total;
                                            let percentage = Math.round((value / total) * 100) + "%";
                                            return ` ${value} Grupos (${percentage})`;
                                        },
                                        title: function(context) {
                                            return `Estado: ${context[0].label}`;
                                        }
                                    }
                                }
                            },
                            cutout: '65%', // Dona más fina y elegante
                            layout: { padding: 10 }
                        }
                    });
                }

                // --------------------------------------------------
                // GRÁFICO 2: TOP CURSOS (Con Nombre Completo)
                // --------------------------------------------------
                const courseCanvas = document.getElementById('courseChart');
                if (courseCanvas) {
                    // Preparamos etiquetas combinadas: "Código - Nombre..."
                    // Si el nombre es muy largo, lo truncamos visualmente en el gráfico
                    const richLabels = (courseData.labels || []).map((code, index) => {
                        const name = courseData.names ? courseData.names[index] : '';
                        // Si existe nombre, mostramos "IS2 - Ingeniería de..."
                        // Si no, solo el código
                        return name ? `${code} - ${name}` : code;
                    });

                    new Chart(courseCanvas, {
                        type: 'bar',
                        data: {
                            labels: richLabels, 
                            datasets: [{
                                label: 'Alumnos Matriculados',
                                data: courseData.data || [],
                                backgroundColor: '#0e7490', // Cyan oscuro profesional
                                borderRadius: 4,
                                barThickness: 20, // Barras más finas
                                maxBarThickness: 30
                            }]
                        },
                        options: {
                            indexAxis: 'y', // Gráfico horizontal para leer mejor los nombres
                            scales: {
                                x: { 
                                    beginAtZero: true, 
                                    grid: { display: false, drawBorder: false },
                                    ticks: { font: { size: 11 } }
                                },
                                y: { 
                                    grid: { display: false, drawBorder: false },
                                    ticks: {
                                        font: { size: 11, weight: '500' },
                                        // Truco: Si el texto es muy largo, Chart.js lo corta, 
                                        // pero con este callback podemos controlar un poco mejor si fuera necesario.
                                        callback: function(value, index) {
                                            const label = this.getLabelForValue(value);
                                            // Truncar si pasa de 25 caracteres para que no ocupe todo el ancho
                                            return label.length > 25 ? label.substr(0, 25) + '...' : label;
                                        }
                                    }
                                }
                            },
                            plugins: {
                                legend: { display: false },
                                tooltip: {
                                    backgroundColor: 'rgba(15, 23, 42, 0.9)', // Azul oscuro casi negro
                                    padding: 12,
                                    titleFont: { size: 13 },
                                    bodyFont: { size: 13 },
                                    callbacks: {
                                        title: function(context) {
                                            // En el tooltip sí mostramos el nombre COMPLETO sin cortes
                                            const index = context[0].dataIndex;
                                            const code = courseData.labels[index];
                                            const name = courseData.names ? courseData.names[index] : '';
                                            return `${code} - ${name}`;
                                        },
                                        label: function(context) {
                                            return ` ${context.raw} Estudiantes matriculados`;
                                        }
                                    }
                                }
                            }
                        }
                    });
                }

                // --------------------------------------------------
                // GRÁFICO 3: CARGA DOCENTE
                // --------------------------------------------------
                const profCanvas = document.getElementById('professorsChart');
                if (profCanvas) {
                    new Chart(profCanvas, {
                        type: 'bar',
                        data: {
                            labels: professorsData.labels || [],
                            datasets: [{
                                label: 'Horas Lectivas Semanales',
                                data: professorsData.data || [],
                                backgroundColor: 'rgba(139, 92, 246, 0.8)', // Purple con transparencia
                                borderColor: '#7c3aed',
                                borderWidth: 1,
                                borderRadius: 4,
                                barThickness: 25
                            }]
                        },
                        options: {
                            responsive: true,
                            plugins: { 
                                legend: { display: false },
                                tooltip: {
                                    callbacks: {
                                        label: function(context) {
                                            return ` ${context.raw} horas / semana`;
                                        }
                                    }
                                }
                            },
                            scales: { 
                                y: { 
                                    beginAtZero: true, 
                                    title: { display: true, text: 'Horas Asignadas' },
                                    grid: { borderDash: [2, 4], color: '#e2e8f0' } // Líneas punteadas sutiles
                                },
                                x: { 
                                    grid: { display: false } 
                                }
                            }
                        }
                    });
                }

            } catch (error) {
                console.error("Error inicializando gráficos:", error);
            }
        }
    };

    initCharts();
});