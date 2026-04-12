/**
 * DATE TODAY BUTTON
 * Agrega funcionalidad a los botones "Hoy" para campos de fecha
 */

function setupFechaHoyButtons() {
    const botones = document.querySelectorAll('.btn-fecha-hoy');
    console.log('Botones fecha encontrados:', botones.length);
    
    botones.forEach((boton, i) => {
        boton.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            console.log('Click en botón fecha', i);
            
            // Buscar el input de fecha en el mismo input-group
            const inputGroup = this.closest('.input-group');
            let campoFecha = null;
            
            if (inputGroup) {
                // Buscar input con type="date"
                campoFecha = inputGroup.querySelector('input[type="date"]');
                
                // Si no encuentra, buscar el primer input
                if (!campoFecha) {
                    campoFecha = inputGroup.querySelector('input');
                }
            }
            
            if (campoFecha) {
                const hoy = new Date();
                const año = hoy.getFullYear();
                const mes = String(hoy.getMonth() + 1).padStart(2, '0');
                const día = String(hoy.getDate()).padStart(2, '0');
                const fechaFormato = `${año}-${mes}-${día}`;
                
                campoFecha.value = fechaFormato;
                campoFecha.dispatchEvent(new Event('change', { bubbles: true }));
                
                // Animación
                campoFecha.style.backgroundColor = '#e8f5e9';
                setTimeout(() => {
                    campoFecha.style.backgroundColor = '';
                }, 300);
                
                campoFecha.focus();
                console.log('Fecha establecida a:', fechaFormato);
            } else {
                console.warn('No se encontró campo de fecha');
            }
        });
    });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupFechaHoyButtons);
} else {
    setupFechaHoyButtons();
}
