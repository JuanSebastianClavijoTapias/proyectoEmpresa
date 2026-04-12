/**
 * TIME NOW BUTTON
 * Agrega funcionalidad a los botones "Actual" para campos de hora
 */

function setupHoraActualButtons() {
    const botones = document.querySelectorAll('.btn-hora-actual');
    console.log('Botones hora encontrados:', botones.length);
    
    botones.forEach((boton, i) => {
        boton.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            console.log('Click en botón hora', i);
            
            // Buscar el input de hora en el mismo input-group
            const inputGroup = this.closest('.input-group');
            let campoHora = null;
            
            if (inputGroup) {
                // Buscar input con type="time"
                campoHora = inputGroup.querySelector('input[type="time"]');
                
                // Si no encuentra, buscar el primer input
                if (!campoHora) {
                    campoHora = inputGroup.querySelector('input');
                }
            }
            
            if (campoHora) {
                const ahora = new Date();
                const horas = String(ahora.getHours()).padStart(2, '0');
                const minutos = String(ahora.getMinutes()).padStart(2, '0');
                const horaFormato = `${horas}:${minutos}`;
                
                campoHora.value = horaFormato;
                campoHora.dispatchEvent(new Event('change', { bubbles: true }));
                
                // Animación
                campoHora.style.backgroundColor = '#e3f2fd';
                setTimeout(() => {
                    campoHora.style.backgroundColor = '';
                }, 300);
                
                campoHora.focus();
                console.log('Hora establecida a:', horaFormato);
            } else {
                console.warn('No se encontró campo de hora');
            }
        });
    });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupHoraActualButtons);
} else {
    setupHoraActualButtons();
}
