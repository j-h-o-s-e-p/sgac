/**
 * Lógica para Matrícula de Laboratorios - Estudiante
 * Requiere: SweetAlert2
 */

document.addEventListener('DOMContentLoaded', function() {
    initEnrollmentSystem();
});

function initEnrollmentSystem() {
    const modalElement = document.getElementById('confirmPostulationModal');
    if (!modalElement) return; // Si no hay modal, no ejecutamos nada

    const modal = new bootstrap.Modal(modalElement);
    const confirmBtn = document.getElementById('btnConfirmPostulation');
    
    // Variables de estado
    let currentCampaignId = null;
    let currentLabId = null;
    
    // 1. Configurar botones de "Postular" en las tarjetas
    document.querySelectorAll('.btn-postulate').forEach(btn => {
        btn.addEventListener('click', function() {
            // Capturar datos del dataset del botón HTML
            currentCampaignId = this.dataset.campaignId;
            currentLabId = this.dataset.labId;
            const courseName = this.dataset.courseName;
            const labName = this.dataset.labName;
            
            // UI del Modal: Llenar datos básicos
            document.getElementById('modalCourseName').textContent = courseName;
            document.getElementById('modalLabName').textContent = labName;
            
            // UI del Modal: Resetear detalles mientras carga
            document.getElementById('modalLabDay').textContent = 'Cargando...';
            document.getElementById('modalLabTime').textContent = '--:--';
            document.getElementById('modalLabRoom').textContent = '...';
            
            modal.show();
            
            // Obtener detalles completos vía AJAX (GET)
            // Reemplazamos el '0' placeholder por el ID real
            const urlDetailsBase = this.dataset.urlDetails; 
            const fetchUrl = urlDetailsBase.replace('0', currentLabId);

            fetch(fetchUrl)
                .then(res => {
                    if (!res.ok) throw new Error('Error de red');
                    return res.json();
                })
                .then(data => {
                    if (data.success) {
                        document.getElementById('modalLabDay').textContent = data.lab.day;
                        document.getElementById('modalLabTime').textContent = 
                            `${data.lab.start_time} - ${data.lab.end_time}`;
                        document.getElementById('modalLabRoom').textContent = data.lab.room;
                    }
                })
                .catch(err => {
                    console.error('Error cargando detalles:', err);
                    document.getElementById('modalLabDay').innerHTML = '<span class="text-danger">Error al cargar info</span>';
                });
        });
    });
    
    // 2. Configurar botón de confirmación (POST)
    confirmBtn.addEventListener('click', function() {
        const btn = this;
        const originalText = btn.innerHTML;
        const postUrl = btn.dataset.urlPostulate;
        
        // Estado de carga visual
        btn.disabled = true;
        btn.classList.add('btn-loading');
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Procesando...';
        
        fetch(postUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                campaign_id: currentCampaignId,
                lab_id: currentLabId
            })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                // EXITO: SweetAlert
                modal.hide();
                Swal.fire({
                    title: '¡Postulación Exitosa!',
                    text: 'Tu solicitud ha sido registrada correctamente. Te avisaremos cuando se confirme la asignación.',
                    icon: 'success',
                    confirmButtonColor: '#198754', // Bootstrap success color
                    confirmButtonText: 'Entendido'
                }).then((result) => {
                    // Recargar página al cerrar la alerta
                    window.location.reload();
                });
                
            } else {
                // ERROR DE NEGOCIO (Ej: Cupos llenos): SweetAlert
                // No cerramos el modal, solo mostramos el error y reseteamos el botón
                const errorMsg = data.errors ? data.errors.join(', ') : 'Ocurrió un error desconocido';
                
                Swal.fire({
                    title: 'No se pudo postular',
                    text: errorMsg,
                    icon: 'warning',
                    confirmButtonColor: '#ffc107',
                    confirmButtonText: 'Revisar'
                });
                
                resetButton(btn, originalText);
            }
        })
        .catch(err => {
            // ERROR DE RED/SERVIDOR: SweetAlert
            console.error(err);
            modal.hide();
            Swal.fire({
                title: 'Error de Sistema',
                text: 'Hubo un problema de conexión. Por favor intenta nuevamente.',
                icon: 'error',
                confirmButtonColor: '#dc3545'
            });
            resetButton(btn, originalText);
        });
    });
}

function resetButton(btn, html) {
    btn.disabled = false;
    btn.classList.remove('btn-loading');
    btn.innerHTML = html;
}

// Función auxiliar de Django para CSRF
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