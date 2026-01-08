document.addEventListener('DOMContentLoaded', function() {
    
    // ==========================================================
    // 0. HELPERS GLOBALES
    // ==========================================================
    
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // ==========================================================
    // 1. INTERFAZ GENERAL Y UI
    // ==========================================================

    // A. Auto-estilizado de formularios
    const classroomForm = document.getElementById('classroomForm');
    if (classroomForm) {
        const inputs = classroomForm.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            if (!['checkbox', 'radio', 'hidden'].includes(input.type)) {
                input.classList.add(input.tagName === 'SELECT' ? 'form-select' : 'form-control');
            }
        });
    }

    // B. Auto-ocultar alertas
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent, .conflict-alert)');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });

    // C. Modal Genérico de Eliminación
    const deleteModal = document.getElementById('confirmDeleteModal');
    if (deleteModal) {
        deleteModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            const deleteUrl = button.dataset.url;
            const name = button.dataset.name;
            
            const deleteForm = deleteModal.querySelector('#deleteForm');
            const nameEl = deleteModal.querySelector('#modalClassroomName, #modalLabName');
            
            if(deleteForm) deleteForm.action = deleteUrl;
            if(nameEl) nameEl.textContent = name;
        });
    }

    // ==========================================================
    // 2. GESTIÓN DE LABORATORIOS
    // ==========================================================

    // A. Calcular capacidad sugerida
    document.querySelectorAll('.btn-toggle-lab-form').forEach(btn => {
        btn.addEventListener('click', function() {
            const courseId = this.dataset.courseId;
            const enrollment = parseInt(this.dataset.enrollment || 0);
            const needed = parseInt(this.dataset.needed || 1);
            
            const suggested = Math.ceil(enrollment / needed);
            const form = document.getElementById(`form-${courseId}`);
            
            if (form) {
                const capacityInput = form.querySelector('.capacity-input');
                const suggestedSpan = form.querySelector('.suggested-capacity');
                
                if (capacityInput && !capacityInput.value) capacityInput.value = suggested;
                if (suggestedSpan) suggestedSpan.textContent = suggested;
            }
        });
    });

    // B. Toggle Profesor Interno/Externo
    document.querySelectorAll('.prof-type-radio').forEach(radio => {
        radio.addEventListener('change', function() {
            const form = this.closest('form');
            const targetType = this.value;
            
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

    // C. Verificación de Conflictos (Labs)
    document.body.addEventListener('change', function(e) {
        if (e.target.classList.contains('lab-schedule-input')) {
            const form = e.target.closest('form');
            checkLabConflicts(form);
        }
    });

    function checkLabConflicts(form) {
        if (!form) return;

        const courseId = form.dataset.courseId;
        const day = form.querySelector('[name="day_of_week"]').value;
        const startTime = form.querySelector('[name="start_time"]').value;
        const endTime = form.querySelector('[name="end_time"]').value;
        const roomId = form.querySelector('[name="room_id"]').value;
        const urlInput = document.getElementById('url-check-conflicts');
        
        if (!day || !startTime || !endTime || !urlInput) return;

        const alertBox = form.querySelector('.conflict-alert');
        const messageBox = form.querySelector('.conflict-message');
        const iconBox = form.querySelector('.alert-icon');
        
        alertBox.classList.remove('d-none', 'alert-danger', 'alert-success');
        alertBox.classList.add('alert-info');
        messageBox.textContent = 'Verificando disponibilidad...';

        let csrfToken = form.querySelector('[name="csrfmiddlewaretoken"]')?.value || getCookie('csrftoken');

        fetch(urlInput.value, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
            body: JSON.stringify({
                course_id: courseId, day_of_week: day, start_time: startTime, end_time: endTime, room_id: roomId
            })
        })
        .then(res => res.json())
        .then(data => {
            alertBox.classList.remove('alert-info');
            if (data.has_conflict) {
                alertBox.classList.add('alert-danger');
                if(iconBox) iconBox.className = 'bi bi-exclamation-triangle-fill me-2 alert-icon';
                messageBox.innerHTML = `<strong>Conflicto:</strong> ${data.messages.join(', ')}`;
            } else {
                alertBox.classList.add('alert-success');
                if(iconBox) iconBox.className = 'bi bi-check-circle-fill me-2 alert-icon';
                messageBox.textContent = 'Horario disponible.';
            }
        })
        .catch(err => {
            console.error(err);
            alertBox.classList.add('alert-warning');
            messageBox.textContent = 'Error verificando conflictos.';
        });
    }

    // D. Actualización status campañas
    const activeCampaigns = document.querySelectorAll('[data-course-id]');
    if (activeCampaigns.length > 0) {
        setInterval(() => {
            activeCampaigns.forEach(card => {
                const courseId = card.dataset.courseId;
                if (typeof updateCampaignStatus === 'function') updateCampaignStatus(courseId);
            });
        }, 30000);
    }

    // ==========================================================
    // 3. PROGRAMACIÓN DE HORARIOS (TEORÍA)
    // ==========================================================
    const scheduleModalEl = document.getElementById('scheduleModal');
    let scheduleModalInstance = null;
    
    if (scheduleModalEl) {
        scheduleModalInstance = new bootstrap.Modal(scheduleModalEl);
        const entriesContainer = document.getElementById('schedule-entries-container');
        const addBtn = document.getElementById('add-schedule-entry');
        const saveBtn = document.getElementById('btn-save-schedule');
        const errorMsg = document.getElementById('modal-error-message');
        const template = document.getElementById('schedule-entry-template');

        const createRow = (data = null) => {
            const clone = template.content.cloneNode(true);
            const row = clone.querySelector('.schedule-entry');
            const daySelect = row.querySelector('.field-day');
            const roomSelect = row.querySelector('.field-room');
            const startInput = row.querySelector('.field-start');
            const endInput = row.querySelector('.field-end');
            
            if (data) {
                daySelect.value = data.day_of_week;
                roomSelect.value = data.room_id || ""; 
                startInput.value = data.start_time;
                endInput.value = data.end_time;
            }
            row.querySelector('.btn-remove-entry').addEventListener('click', () => row.remove());
            entriesContainer.appendChild(row);
        };

        document.querySelectorAll('.btn-edit-schedule').forEach(btn => {
            btn.addEventListener('click', function() {
                const groupId = this.dataset.groupId;
                const groupName = this.dataset.groupName;
                entriesContainer.innerHTML = '';
                errorMsg.classList.add('d-none');
                document.getElementById('modal_course_group_id').value = groupId;
                document.getElementById('modal-group-name-title').textContent = groupName;
                
                let schedules = [];
                try {
                    const rawJson = this.dataset.schedules;
                    if (rawJson && rawJson !== "None") schedules = JSON.parse(rawJson);
                } catch (e) { console.error(e); }
                
                if (schedules && schedules.length > 0) schedules.forEach(s => createRow(s));
                else createRow();
                
                scheduleModalInstance.show();
            });
        });

        if(addBtn) addBtn.addEventListener('click', () => createRow());

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
                    
                    if (!day || !room || !start || !end) { hasError = true; return; }
                    if (start >= end) { hasError = true; alert('La hora de inicio debe ser menor a la hora fin.'); return; }
                    horarios.push({ day, room_id: room, start_time: start, end_time: end });
                });
                
                if (hasError) {
                    errorMsg.textContent = "Completa todos los campos correctamente.";
                    errorMsg.classList.remove('d-none');
                    return;
                }

                const url = document.getElementById('api-save-schedule-url').value;
                const groupId = document.getElementById('modal_course_group_id').value;

                fetch(url, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                    body: JSON.stringify({ course_group_id: groupId, horarios: horarios })
                })
                .then(res => res.json())
                .then(data => {
                    if (data.success) location.reload();
                    else {
                        errorMsg.textContent = data.error || "Error al guardar.";
                        errorMsg.classList.remove('d-none');
                    }
                })
                .catch(() => {
                    errorMsg.textContent = "Error de conexión.";
                    errorMsg.classList.remove('d-none');
                });
            });
        }
    }

    // ==========================================================
    // 4. BUSCADOR DE REPORTES
    // ==========================================================
    const searchInput = document.getElementById('gradeReportSearch');
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            const filter = this.value.toLowerCase();
            const rows = document.querySelectorAll('#groupsTable .group-row');
            let hasVisible = false;
            rows.forEach(row => {
                const text = row.innerText.toLowerCase();
                const visible = text.includes(filter);
                row.style.display = visible ? '' : 'none';
                if (visible) hasVisible = true;
            });
            const noResMsg = document.getElementById('noResultsMessage');
            const table = document.getElementById('groupsTable');
            if (noResMsg) {
                noResMsg.classList.toggle('d-none', hasVisible);
                if(table) table.classList.toggle('d-none', !hasVisible);
            }
        });
    }

    // ==========================================================
    // 5. GRÁFICOS DASHBOARD (Chart.js)
    // ==========================================================
    const initCharts = () => {
        const saturationEl = document.getElementById('data-saturation');
        if (saturationEl && typeof Chart !== 'undefined') {
            try {
                const parseDjangoData = (id) => {
                    const el = document.getElementById(id);
                    if (!el) return null;
                    try {
                        let content = JSON.parse(el.textContent);
                        if (typeof content === 'string') content = JSON.parse(content);
                        return content;
                    } catch(e) { return null; }
                };

                const saturationData = parseDjangoData('data-saturation');
                const courseData = parseDjangoData('data-courses');
                const professorsData = parseDjangoData('data-professors');

                Chart.defaults.font.family = "'Segoe UI', sans-serif";
                Chart.defaults.color = '#64748b';
                Chart.defaults.maintainAspectRatio = false;

                if (document.getElementById('saturationChart')) {
                    new Chart(document.getElementById('saturationChart'), {
                        type: 'doughnut',
                        data: {
                            labels: saturationData.labels,
                            datasets: [{
                                data: saturationData.data,
                                backgroundColor: ['#ef4444', '#10b981', '#f59e0b'],
                                borderWidth: 2, borderColor: '#ffffff'
                            }]
                        },
                        options: { cutout: '65%', plugins: { legend: { position: 'right', labels: { usePointStyle: true } } } }
                    });
                }
                if (document.getElementById('courseChart')) {
                    const richLabels = (courseData.labels || []).map((code, i) => {
                        const name = courseData.names ? courseData.names[i] : '';
                        return name ? `${code} - ${name}` : code;
                    });
                    new Chart(document.getElementById('courseChart'), {
                        type: 'bar',
                        data: {
                            labels: richLabels,
                            datasets: [{ label: 'Alumnos', data: courseData.data, backgroundColor: '#0e7490', borderRadius: 4, barThickness: 20 }]
                        },
                        options: {
                            indexAxis: 'y',
                            scales: {
                                x: { grid: { display: false } },
                                y: { grid: { display: false }, ticks: { callback: function(val) { const label = this.getLabelForValue(val); return label.length > 25 ? label.substr(0, 25) + '...' : label; } } }
                            },
                            plugins: { legend: { display: false } }
                        }
                    });
                }
                if (document.getElementById('professorsChart')) {
                    new Chart(document.getElementById('professorsChart'), {
                        type: 'bar',
                        data: { labels: professorsData.labels, datasets: [{ label: 'Horas Semanales', data: professorsData.data, backgroundColor: 'rgba(139, 92, 246, 0.8)', borderRadius: 4 }] },
                        options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, grid: { borderDash: [2, 4] } } } }
                    });
                }
            } catch (error) { console.error("Error charts:", error); }
        }
    };

    // ==========================================================
    // 6. GESTIÓN DE RESERVAS DE AULAS
    // ==========================================================
    
    // Variables globales de estado
    let currentReservationId = null;
    const approveModalEl = document.getElementById('approveReservationModal');
    const rejectModalEl = document.getElementById('rejectReservationModal');
    
    // Instanciar Modales (Verificación de existencia)
    let approveModalInstance = approveModalEl ? new bootstrap.Modal(approveModalEl) : null;
    let rejectModalInstance = rejectModalEl ? new bootstrap.Modal(rejectModalEl) : null;

    // Delegación de Eventos (Clics globales)
    document.addEventListener('click', function(e) {
        
        // Botón APROBAR
        const btnApprove = e.target.closest('.btn-approve-reservation');
        if (btnApprove) {
            e.preventDefault();
            currentReservationId = btnApprove.dataset.id;
            if (approveModalInstance) approveModalInstance.show();
        }

        // Botón RECHAZAR
        const btnReject = e.target.closest('.btn-reject-reservation');
        if (btnReject) {
            e.preventDefault();
            currentReservationId = btnReject.dataset.id;
            const reasonInput = document.getElementById('rejectionReasonInput');
            if(reasonInput) reasonInput.value = '';
            if (rejectModalInstance) rejectModalInstance.show();
        }
    });

    // Lógica: Confirmar APROBACIÓN
    const btnConfirmApprove = document.getElementById('btnConfirmApproveReservation');
    if (btnConfirmApprove) {
        btnConfirmApprove.addEventListener('click', async function() {
            if (!currentReservationId) return;

            const originalText = this.innerHTML;
            this.disabled = true;
            this.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Procesando...';

            try {
                const response = await fetch('/secretaria/classroom-reservations/approve/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                    body: JSON.stringify({ reservation_id: currentReservationId })
                });
                const data = await response.json();

                if (data.success) {
                    if (approveModalInstance) approveModalInstance.hide();
                    location.reload(); 
                } else {
                    alert('Error: ' + data.error);
                }
            } catch (error) {
                console.error(error);
                alert('Error de conexión.');
            } finally {
                this.disabled = false;
                this.innerHTML = originalText;
            }
        });
    }

    // Lógica: Confirmar RECHAZO
    const btnConfirmReject = document.getElementById('btnConfirmRejectReservation');
    if (btnConfirmReject) {
        btnConfirmReject.addEventListener('click', async function() {
            if (!currentReservationId) return;
            const reason = document.getElementById('rejectionReasonInput')?.value || '';

            const originalText = this.innerHTML;
            this.disabled = true;
            this.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Procesando...';

            try {
                const response = await fetch('/secretaria/classroom-reservations/reject/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                    body: JSON.stringify({ reservation_id: currentReservationId, reason: reason })
                });
                const data = await response.json();

                if (data.success) {
                    if (rejectModalInstance) rejectModalInstance.hide();
                    location.reload();
                } else {
                    alert('Error: ' + data.error);
                }
            } catch (error) {
                console.error(error);
                alert('Error de conexión.');
            } finally {
                this.disabled = false;
                this.innerHTML = originalText;
            }
        });
    }

    // Inicializar gráficos al final
    initCharts();
});
