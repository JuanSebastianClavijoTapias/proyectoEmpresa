"""
EJEMPLOS DE CONSUMO DE API DEL KANBAN BOARD

Este archivo contiene ejemplos de cómo consumir la API del Kanban desde:
1. Python (requests)
2. JavaScript/AJAX
3. React
4. cURL
"""

# ============================================================================
# 1. EJEMPLOS CON PYTHON (usando requests)
# ============================================================================

"""
Instalación:
pip install requests

Uso básico:
"""

import requests
import json

BASE_URL = "http://localhost:8000"
SESSION = requests.Session()

# ============================================================================
# Autenticación (si usas token)
# ============================================================================

def autenticar_usuario(username, password):
    """
    Obtiene token de autenticación (si usas Django REST Framework con TokenAuth)
    """
    response = requests.post(
        f"{BASE_URL}/api/auth/login/",
        json={"username": username, "password": password}
    )
    if response.status_code == 200:
        token = response.json().get("token")
        SESSION.headers.update({"Authorization": f"Token {token}"})
        print(f"✅ Autenticado como {username}")
        return token
    else:
        print(f"❌ Error de autenticación: {response.text}")
        return None

# ============================================================================
# Ejemplo 1: Obtener todas las tareas (sin filtros)
# ============================================================================

def obtener_tareas():
    """Obtiene todas las tareas agrupadas por estado"""
    try:
        response = SESSION.get(f"{BASE_URL}/tareas/api/kanban/tareas/")
        response.raise_for_status()
        
        data = response.json()
        if data['success']:
            print("✅ Tareas obtenidas correctamente")
            print(f"Total: {data['stats']['total']}")
            print(f"Pendientes: {data['stats']['pendiente']}")
            print(f"En proceso: {data['stats']['en_proceso']}")
            print(f"Completadas: {data['stats']['completado']}")
            print(f"Canceladas: {data['stats']['cancelado']}")
            
            return data['data']
        else:
            print(f"❌ Error en la API: {data['error']}")
            return None
            
    except requests.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return None


# ============================================================================
# Ejemplo 2: Obtener tareas con filtros
# ============================================================================

def obtener_tareas_filtradas(cliente=None, placa=None, prioridad=None):
    """Obtiene tareas con filtros aplicados"""
    params = {}
    if cliente:
        params['filtro_cliente'] = cliente
    if placa:
        params['filtro_placa'] = placa
    if prioridad:
        params['filtro_prioridad'] = prioridad
    
    try:
        response = SESSION.get(
            f"{BASE_URL}/tareas/api/kanban/tareas/",
            params=params
        )
        response.raise_for_status()
        
        data = response.json()
        if data['success']:
            print(f"✅ Tareas filtradas obtenidas ({data['stats']['total']} total)")
            return data['data']
        else:
            print(f"❌ Error: {data['error']}")
            return None
            
    except requests.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return None


# Ejemplos de uso:
# tareas = obtener_tareas_filtradas(cliente="Juan", prioridad="urgente")
# tareas = obtener_tareas_filtradas(placa="ABC-123")


# ============================================================================
# Ejemplo 3: Mover una tarea a otro estado
# ============================================================================

def mover_tarea(tarea_id, nuevo_estado):
    """
    Mueve una tarea a un nuevo estado
    
    Estados válidos: pendiente, en_proceso, completado, cancelado
    """
    estados_validos = ['pendiente', 'en_proceso', 'completado', 'cancelado']
    
    if nuevo_estado not in estados_validos:
        print(f"❌ Estado inválido. Debe ser uno de: {', '.join(estados_validos)}")
        return None
    
    try:
        response = SESSION.post(
            f"{BASE_URL}/tareas/api/kanban/tareas/{tarea_id}/estado/",
            json={"nuevo_estado": nuevo_estado},
            headers={"X-CSRFToken": obtener_csrf_token()}
        )
        response.raise_for_status()
        
        data = response.json()
        if data['success']:
            print(f"✅ Tarea #{tarea_id} movida a '{nuevo_estado}'")
            print(f"   Mensaje: {data['message']}")
            return data['tarea']
        else:
            print(f"❌ Error: {data['error']}")
            return None
            
    except requests.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return None


# Ejemplo de uso:
# mover_tarea(42, 'completado')
# mover_tarea(15, 'en_proceso')


# ============================================================================
# Ejemplo 4: Reordenar múltiples tareas
# ============================================================================

def reordenar_tareas(tareas_config):
    """
    Reordena múltiples tareas en una sola petición
    
    Args:
        tareas_config (list): Lista de dicts con {'id', 'estado', 'orden'}
    """
    try:
        response = SESSION.post(
            f"{BASE_URL}/tareas/api/kanban/reordenar/",
            json={"tareas": tareas_config},
            headers={"X-CSRFToken": obtener_csrf_token()}
        )
        response.raise_for_status()
        
        data = response.json()
        if data['success']:
            print(f"✅ {data['message']}")
            return True
        else:
            print(f"❌ Error: {data['error']}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False


# Ejemplo de uso:
# config = [
#     {'id': 1, 'estado': 'pendiente', 'orden': 1},
#     {'id': 2, 'estado': 'pendiente', 'orden': 2},
#     {'id': 5, 'estado': 'completado', 'orden': 1},
# ]
# reordenar_tareas(config)


# ============================================================================
# Ejemplo 5: Script completo de automatización
# ============================================================================

def procesar_tareas_urgentes():
    """
    Script de ejemplo: Procesa todas las tareas urgentes
    - Las que están vencidas → Canceladas
    - Las que vencen hoy → En proceso
    """
    tareas = obtener_tareas_filtradas(prioridad='urgente')
    
    if not tareas:
        print("No hay tareas urgentes")
        return
    
    for estado, lista_tareas in tareas.items():
        for tarea in lista_tareas:
            dias_restantes = tarea['dias_restantes']
            tarea_id = tarea['id']
            cliente = tarea['cliente']
            
            if dias_restantes < 0:
                print(f"🔴 Tarea #{tarea_id} ({cliente}) VENCIDA → Cancelando...")
                mover_tarea(tarea_id, 'cancelado')
                
            elif dias_restantes == 0:
                print(f"🟡 Tarea #{tarea_id} ({cliente}) Entrega HOY → En proceso...")
                mover_tarea(tarea_id, 'en_proceso')


# ============================================================================
# Funciones auxiliares
# ============================================================================

def obtener_csrf_token():
    """Obtiene el CSRF token de la página de inicio"""
    try:
        response = requests.get(f"{BASE_URL}/")
        # En una aplicación real, extraerías esto del formulario/metadata
        # Por ahora retornamos vacío (si usas CSRF_TRUSTED_ORIGINS en settings)
        return ""
    except:
        return ""


def contar_tareas_por_estado():
    """Cuenta cuántas tareas hay en cada estado"""
    tareas = obtener_tareas()
    
    if tareas:
        for estado, lista in tareas.items():
            print(f"{estado.upper()}: {len(lista)} tareas")


def mostrar_tareas_sin_pagar():
    """Muestra tareas con saldo pendiente"""
    tareas = obtener_tareas()
    
    if not tareas:
        return
    
    print("\n💰 TAREAS CON SALDO PENDIENTE:\n")
    total_deuda = 0
    
    for estado, lista in tareas.items():
        for tarea in lista:
            if tarea['saldo_pendiente'] > 0:
                print(f"#{tarea['id']} | {tarea['cliente']} | "
                      f"${tarea['saldo_pendiente']:.2f} pendiente | "
                      f"{tarea['porcentaje_pago']}% pagado")
                total_deuda += tarea['saldo_pendiente']
    
    print(f"\n📊 Total en deuda: ${total_deuda:.2f}")


# ============================================================================
# Script de prueba
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("EJEMPLOS DE CONSUMO API - KANBAN BOARD")
    print("=" * 60)
    
    # Descomentar para usar:
    
    # 1. Obtener todas las tareas
    # print("\n1️⃣  Obteniendo todas las tareas...")
    # obtener_tareas()
    
    # 2. Obtener tareas con filtros
    # print("\n2️⃣  Obteniendo tareas urgentes...")
    # tareas = obtener_tareas_filtradas(prioridad='urgente')
    
    # 3. Contar tareas por estado
    # print("\n3️⃣  Contando tareas por estado...")
    # contar_tareas_por_estado()
    
    # 4. Mostrar tareas sin pagar
    # print("\n4️⃣  Tareas con saldo pendiente...")
    # mostrar_tareas_sin_pagar()
    
    # 5. Mover una tarea (cambiar el ID según tus datos)
    # print("\n5️⃣  Moviendo tarea #1 a 'completado'...")
    # mover_tarea(1, 'completado')
    
    print("\n✅ Para usar estos ejemplos, descomenta la sección al final del script")
