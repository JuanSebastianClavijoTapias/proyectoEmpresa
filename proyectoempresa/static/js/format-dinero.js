/**
 * UTILIDADES DE FORMATEO DE DINERO
 * Funciones para formatear valores monetarios en el frontend
 * Formato: 1.234.567,89 (latino)
 */

/**
 * Formatea un número como dinero con separadores de miles
 * @param {number|string} valor - El valor a formatear
 * @param {number} decimales - Cantidad de decimales a mostrar (default: 0)
 * @returns {string} Valor formateado
 * 
 * Ejemplos:
 *   formatoDinero(1234567.89)      --> "1.234.567"
 *   formatoDinero(1234567.89, 2)   --> "1.234.567,89"
 *   formatoDinero(5000)             --> "5.000"
 */
function formatoDinero(valor, decimales = 0) {
    if (valor === null || valor === undefined) {
        return '0';
    }
    
    try {
        let num;
        if (typeof valor === 'number') {
            num = valor;
        } else {
            // String: quitar TODOS los puntos (miles) y cambiar coma por punto (decimal)
            num = parseFloat(String(valor).replace(/\./g, '').replace(',', '.'));
        }
        
        if (isNaN(num)) {
            return String(valor);
        }
        
        // Redondear si es necesario
        num = Math.round(num * Math.pow(10, decimales)) / Math.pow(10, decimales);
        
        // Separar parte entera y decimal
        let partes = num.toFixed(decimales).split('.');
        let parteEntera = partes[0];
        let parteDecimal = partes[1] || '';
        
        // Formatear parte entera con puntos como separadores
        parteEntera = parteEntera.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
        
        // Reconstruir
        if (decimales > 0 && parteDecimal) {
            return parteEntera + ',' + parteDecimal;
        }
        return parteEntera;
    } catch (e) {
        console.warn('Error formateando dinero:', e);
        return String(valor);
    }
}

/**
 * Formatea múltiples valores de dinero en el DOM
 * Busca elementos con la clase 'money-format' y les aplica el formato
 * 
 * Uso en HTML:
 *   <span class="money-format" data-decimales="2">1234567.89</span>
 *   <!-- Resultado: "1.234.567,89" -->
 */
function formatearDineroEnDOM() {
    document.querySelectorAll('.money-format').forEach(elemento => {
        const valor = elemento.textContent;
        const decimales = parseInt(elemento.dataset.decimales) || 0;
        elemento.textContent = formatoDinero(valor, decimales);
    });
}

/**
 * Formatea un valor de dinero con símbolo de moneda
 * @param {number|string} valor - El valor a formatear
 * @param {string} moneda - Símbolo o código de moneda (default: '$')
 * @param {number} decimales - Decimales a mostrar (default: 2)
 * @returns {string} Valor con símbolo
 * 
 * Ejemplos:
 *   formatoMoneda(1234567.89)              --> "$1.234.567,89"
 *   formatoMoneda(1234567.89, 'USD', 2)   --> "1.234.567,89 USD"
 */
function formatoMoneda(valor, moneda = '$', decimales = 2) {
    const formateado = formatoDinero(valor, decimales);
    return `${moneda} ${formateado}`;
}

/**
 * Parsea un string formateado de dinero a número
 * @param {string} valor - String en formato "1.234.567,89"
 * @returns {number} Número parseado
 * 
 * Ejemplos:
 *   parsearDinero("1.234.567,89")  --> 1234567.89
 *   parsearDinero("5.000")         --> 5000
 */
function parsearDinero(valor) {
    if (!valor) return 0;
    
    return parseFloat(
        String(valor)
            .replace(/\./g, '')      // Quitar puntos (separadores de miles)
            .replace(',', '.')       // Cambiar coma por punto (decimal)
    );
}

/**
 * Verifica si un número tiene más de 6 dígitos (>= 1.000.000)
 * @param {number|string} valor - Valor a verificar
 * @returns {boolean} True si >= 1.000.000
 */
function esGrande(valor, limite = 1000000) {
    try {
        let num;
        if (typeof valor === 'number') {
            num = valor;
        } else {
            num = parseFloat(String(valor).replace(/\./g, '').replace(',', '.'));
        }
        return num >= limite;
    } catch (e) {
        return false;
    }
}

// Ejecutar formateo cuando el DOM está listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', formatearDineroEnDOM);
} else {
    formatearDineroEnDOM();
}

// Exportar para módulos si es necesario
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        formatoDinero,
        formatoMoneda,
        parsearDinero,
        esGrande,
        formatearDineroEnDOM
    };
}
