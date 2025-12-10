document.addEventListener('DOMContentLoaded', function() {
    
    // ==========================================================
    // SECCIÓN 1: CÓDIGO ORIGINAL (BASE COMPARTIDA / ALUMNO)
    // ==========================================================

    // 1. HELPERS Y UTILIDADES (CSRF Token para Django)
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

    // Activación de Tooltips (Bootstrap)
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // 2. LÓGICA DE PERFIL (MODAL CAMBIO DE CONTRASEÑA)
    const modal = document.getElementById('changePasswordModal');
    if (modal) {
        const form = document.getElementById('changePasswordForm');
        const oldPassInput = document.getElementById('old_password');
        const newPassInput = document.getElementById('new_password');
        const confirmPassInput = document.getElementById('confirm_password');
        const btnSave = document.getElementById('btnSavePassword');
        const globalError = document.getElementById('modal-global-error');

        function clearErrors() {
            globalError.classList.add('d-none');
            oldPassInput.classList.remove('is-invalid');
            newPassInput.classList.remove('is-invalid');
            confirmPassInput.classList.remove('is-invalid');
        }

        if(newPassInput) {
            newPassInput.addEventListener('input', function() {
                if (this.value && this.value === oldPassInput.value) {
                    this.classList.add('is-invalid');
                    document.getElementById('error-new-pass').textContent = 'La nueva contraseña no puede ser igual a la actual.';
                } else {
                    this.classList.remove('is-invalid');
                }
            });
        }

        if(btnSave) {
            btnSave.addEventListener('click', function() {
                clearErrors();
                
                if (newPassInput.value !== confirmPassInput.value) {
                    confirmPassInput.classList.add('is-invalid');
                    return;
                }

                const url = form.getAttribute('data-url');
                const csrfToken = getCookie('csrftoken'); 

                const formData = {
                    old_password: oldPassInput.value,
                    new_password: newPassInput.value,
                    confirm_password: confirmPassInput.value
                };

                fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify(formData)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const modalInstance = bootstrap.Modal.getInstance(modal);
                        modalInstance.hide();
                        form.reset();
                        
                        if (typeof Swal !== 'undefined') {
                            Swal.fire({
                                title: '¡Excelente!', text: 'Contraseña actualizada.', icon: 'success',
                                confirmButtonColor: '#2563eb'
                            });
                        } else {
                            alert('Contraseña actualizada correctamente');
                        }
                    } else {
                        if (data.error_type === 'old_password') {
                            oldPassInput.classList.add('is-invalid');
                            document.getElementById('error-old-pass').textContent = data.message;
                        } else {
                            globalError.textContent = data.message;
                            globalError.classList.remove('d-none');
                        }
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    globalError.textContent = 'Error de conexión.';
                    globalError.classList.remove('d-none');
                });
            });
        }
    }

    // 3. LÓGICA DE CURSOS DOCENTE (SÍLABOS Y UPLOAD)
    const uploadSyllabusModal = document.getElementById('uploadModal');
    if (uploadSyllabusModal) {
        uploadSyllabusModal.addEventListener('show.bs.modal', function (event) {
            const button = event.relatedTarget;
            const courseId = button.getAttribute('data-course-id');
            const courseName = button.getAttribute('data-course-name');
            
            const titleEl = uploadSyllabusModal.querySelector('#modalCourseName');
            const form = uploadSyllabusModal.querySelector('#syllabusForm');
            
            if(titleEl) titleEl.textContent = courseName;

            const urlTemplateEl = document.getElementById('url-syllabus-template');
            if(urlTemplateEl && form) {
                const baseUrl = urlTemplateEl.getAttribute('data-url');
                form.action = baseUrl.replace('00000000-0000-0000-0000-000000000000', courseId);
            }
        });
    }

    // 4. LÓGICA DEL MODAL DE PROGRESO (TIMELINE)
    const progressModalEl = document.getElementById('progressModal');
    if (progressModalEl) {
        const progressModal = new bootstrap.Modal(progressModalEl);
        const contentDiv = document.getElementById('progressContent');
        const titleLabel = document.getElementById('progressModalLabel');
        const subtitleLabel = document.getElementById('progressModalSubtitle');

        document.body.addEventListener('click', function(e) {
            const btn = e.target.closest('.btn-view-progress');
            if(btn) {
                const groupId = btn.getAttribute('data-group-id');
                const urlTemplate = btn.getAttribute('data-url-template');

                if(!urlTemplate) return;

                const url = urlTemplate.replace('00000000-0000-0000-0000-000000000000', groupId);

                titleLabel.textContent = "Cargando...";
                subtitleLabel.textContent = "Conectando...";
                contentDiv.innerHTML = `<div class="text-center py-5 text-muted"><div class="spinner-border text-primary mb-2"></div><p>Obteniendo datos...</p></div>`;
                progressModal.show();

                fetch(url)
                    .then(res => res.json())
                    .then(data => {
                        if (data.error) {
                            contentDiv.innerHTML = `<div class="alert alert-warning text-center">${data.error}</div>`;
                            return;
                        }
                        
                        titleLabel.textContent = data.course_name;
                        subtitleLabel.textContent = data.group_name;

                        let html = '<div class="timeline-wrapper">';
                        if (data.syllabus_data && data.syllabus_data.length > 0) {
                            data.syllabus_data.forEach(block => {
                                html += `<div class="timeline-unit-title text-uppercase small"><i class="bi bi-list-stars me-1"></i> ${block.unit_name}</div>`;
                                block.sessions.forEach(session => {
                                    const isDone = session.is_completed;
                                    const itemClass = isDone ? 'completed' : 'pending';
                                    const icon = isDone ? '<i class="bi bi-check-lg fw-bold"></i>' : `<span class="fw-bold small">${session.number}</span>`;
                                    const badge = isDone ? '<span class="badge bg-success float-end">Completado</span>' : '<span class="badge bg-secondary float-end">Pendiente</span>';

                                    html += `
                                    <div class="timeline-item ${itemClass}">
                                        <div class="timeline-marker">${icon}</div>
                                        <div class="timeline-content">
                                            ${badge}
                                            <h6 class="fw-bold mb-1">Sesión ${session.number}</h6>
                                            <p class="mb-0 text-muted small">${session.topic}</p>
                                        </div>
                                    </div>`;
                                });
                            });
                        } else {
                            html += '<div class="alert alert-info">No hay sesiones registradas.</div>';
                        }
                        html += '</div>';
                        contentDiv.innerHTML = html;
                    })
                    .catch(err => {
                        console.error(err);
                        contentDiv.innerHTML = `<div class="text-center py-4 text-danger"><i class="bi bi-bug display-4"></i><p>Error de conexión</p></div>`;
                    });
            }
        });
    }

    // ==========================================================
    // SECCIÓN 2: NUEVAS FUNCIONES (MÓDULO PROFESOR)
    // ==========================================================

    // 5. REGISTRO DE ASISTENCIA Y LIMITES DE TEMAS
    const sessionSelect = document.getElementById('sessionSelect');
    if (sessionSelect) {
        sessionSelect.addEventListener('change', function() {
            const url = new URL(window.location.href);
            url.searchParams.set('date', this.value);
            window.location.href = url.toString();
        });
    }

    const topicsCard = document.getElementById('topicsCard');
    if (topicsCard) {
        const maxAllowed = parseInt(topicsCard.getAttribute('data-quota')) || 0;
        const checkboxes = document.querySelectorAll('.topic-checkbox');

        if (maxAllowed <= 0) {
            checkboxes.forEach(cb => { cb.disabled = true; });
        } else {
            checkboxes.forEach(cb => {
                cb.addEventListener('change', function() {
                    const checkedCount = document.querySelectorAll('.topic-checkbox:checked').length;
                    if (checkedCount > maxAllowed) {
                        this.checked = false;
                        if (typeof Swal !== 'undefined') {
                            Swal.fire({ icon: 'warning', title: 'Límite diario', text: `Solo puedes marcar ${maxAllowed} tema(s) más el día de hoy.`, confirmButtonColor: '#f59e0b' });
                        } else {
                            alert(`Solo puedes marcar ${maxAllowed} tema(s) más hoy.`);
                        }
                    }
                });
            });
        }
    }

    // 6. TABLAS CON SCROLL (DRAG) PARA REPORTES
    const dragScrollContainers = document.querySelectorAll('.table-drag-scroll');
    dragScrollContainers.forEach(container => {
        let isDown = false;
        let startX;
        let scrollLeft;

        container.addEventListener('mousedown', (e) => {
            isDown = true;
            container.classList.add('active');
            startX = e.pageX - container.offsetLeft;
            scrollLeft = container.scrollLeft;
        });
        container.addEventListener('mouseleave', () => { isDown = false; });
        container.addEventListener('mouseup', () => { isDown = false; });
        container.addEventListener('mousemove', (e) => {
            if (!isDown) return;
            e.preventDefault();
            const x = e.pageX - container.offsetLeft;
            const walk = (x - startX) * 2;
            container.scrollLeft = scrollLeft - walk;
        });
        // Navegación con teclado si el mouse entra
        container.addEventListener('mouseenter', () => {
            document.onkeydown = function(e) {
                if (e.key === 'ArrowLeft') container.scrollLeft -= 50;
                if (e.key === 'ArrowRight') container.scrollLeft += 50;
            };
        });
        container.addEventListener('mouseleave', () => { document.onkeydown = null; });
    });

    // 7. GRÁFICOS (CHART.JS) PARA ESTADÍSTICAS
    const labelsElement = document.getElementById('data-labels');
    if (labelsElement) {
        // Recuperar datos
        const labels = JSON.parse(labelsElement.textContent);
        const gradesData = JSON.parse(document.getElementById('data-grades').textContent);
        const attendanceData = JSON.parse(document.getElementById('data-attendance').textContent);
        const countsData = JSON.parse(document.getElementById('data-counts').textContent);

        // Helper para mensaje de "Sin datos"
        function drawNoDataMessage(canvasElement) {
            const ctx = canvasElement.getContext('2d');
            ctx.clearRect(0, 0, canvasElement.width, canvasElement.height);
            ctx.font = "14px 'Segoe UI'";
            ctx.fillStyle = "#858796";
            ctx.textAlign = "center";
            ctx.fillText("No hay datos suficientes", canvasElement.width / 2, canvasElement.height / 2);
        }

        if (typeof Chart !== 'undefined') {
            Chart.defaults.font.family = "'Segoe UI', 'Helvetica Neue', 'Arial', sans-serif";
            Chart.defaults.color = '#858796';

            // Variable global para guardar instancias (útil para redimensionar al imprimir)
            window.myCharts = {};

            // Gráfico Barras
            const ctxCourse = document.getElementById('courseChart');
            if (ctxCourse && labels.length > 0) {
                window.myCharts.courseChart = new Chart(ctxCourse.getContext('2d'), {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [
                            { label: 'Nota Promedio', data: gradesData, backgroundColor: 'rgba(78, 115, 223, 0.8)', borderColor: 'rgba(78, 115, 223, 1)', borderWidth: 1, borderRadius: 4, yAxisID: 'y' },
                            { label: '% Asistencia', data: attendanceData, type: 'line', borderColor: '#1cc88a', backgroundColor: 'rgba(28, 200, 138, 0.1)', borderWidth: 2, pointRadius: 4, tension: 0.3, fill: true, yAxisID: 'y1' }
                        ]
                    },
                    options: {
                        maintainAspectRatio: false, responsive: true,
                        scales: {
                            x: { grid: { display: false } },
                            y: { beginAtZero: true, max: 20, title: { display: true, text: 'Nota' } },
                            y1: { beginAtZero: true, max: 100, position: 'right', grid: { drawOnChartArea: false } }
                        }
                    }
                });
            } else if (ctxCourse) { drawNoDataMessage(ctxCourse); }

            // Gráfico Dona
            const ctxStatus = document.getElementById('statusChart');
            const totalAlumnos = countsData.aprobados + countsData.desaprobados;
            if (ctxStatus && totalAlumnos > 0) {
                window.myCharts.statusChart = new Chart(ctxStatus.getContext('2d'), {
                    type: 'doughnut',
                    data: {
                        labels: ['Aprobados', 'Desaprobados'],
                        datasets: [{ data: [countsData.aprobados, countsData.desaprobados], backgroundColor: ['#1cc88a', '#e74a3b'], hoverBackgroundColor: ['#17a673', '#be2617'], borderWidth: 2, borderColor: '#ffffff' }]
                    },
                    options: { maintainAspectRatio: false, responsive: true, cutout: '75%', plugins: { legend: { display: false } } }
                });
            } else if (ctxStatus) {
                new Chart(ctxStatus.getContext('2d'), { type: 'doughnut', data: { datasets: [{ data: [1], backgroundColor: ['#e3e6f0'], borderWidth: 0 }] }, options: { maintainAspectRatio: false, cutout: '75%', plugins: { tooltip: { enabled: false } } } });
            }
        }
    }

    // 8. EVENTOS DE IMPRESIÓN (REDIMENSIONAR CHARTJS)
    window.onbeforeprint = () => {
        if (window.myCharts) { for (let key in window.myCharts) { window.myCharts[key].resize(); } }
    };
    window.onafterprint = () => {
        if (window.myCharts) { for (let key in window.myCharts) { window.myCharts[key].resize(); } }
    };

});