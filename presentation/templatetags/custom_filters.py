import json
from django import template
from decimal import Decimal

register = template.Library()

# ==========================================
# UTILIDADES DE DICCIONARIOS Y JSON
# ==========================================

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Obtiene un valor de un diccionario manejando conversiones de tipos y JSON strings.
    
    Uso: {{ mi_dict|get_item:clave }}
    
    Estrategia:
    1. Si es None, retorna None.
    2. Si es string, intenta parsearlo como JSON.
    3. Busca la clave exacta.
    4. Si falla, convierte la clave a string (útil para UUIDs).
    5. Si falla, convierte la clave a int (útil para índices numéricos).
    """
    if dictionary is None:
        return None

    # Si el diccionario viene como string (JSON), intentamos convertirlo
    if isinstance(dictionary, str):
        try:
            dictionary = json.loads(dictionary)
        except (ValueError, TypeError):
            return None

    if not isinstance(dictionary, dict):
        return None

    # 1. Búsqueda Directa
    if key in dictionary:
        return dictionary[key]
    
    # 2. Búsqueda como String (Para UUIDs o claves numéricas accedidas como string)
    key_str = str(key)
    if key_str in dictionary:
        return dictionary[key_str]
    
    # 3. Búsqueda como Entero (Si la clave en el dict es int, pero llega como str)
    if key_str.isdigit():
        try:
            key_int = int(key_str)
            if key_int in dictionary:
                return dictionary[key_int]
        except (ValueError, TypeError):
            pass
            
    return None


@register.filter(name='selectattr')
def selectattr(iterable, attr):
    """
    Filtra una lista de objetos o diccionarios, devolviendo solo aquellos
    que contienen el atributo o clave especificada.
    
    Uso: {{ lista_objetos|selectattr:'nombre_atributo' }}
    """
    if not iterable:
        return []
    
    result = []
    for item in iterable:
        # Si es un diccionario
        if isinstance(item, dict):
            if attr in item:
                result.append(item)
        # Si es un objeto (modelo, clase, etc.)
        else:
            if hasattr(item, attr):
                result.append(item)
    
    return result


# ==========================================
# UTILIDADES MATEMÁTICAS Y DE FORMATO
# ==========================================

@register.filter(name='subtract')
def subtract(value, arg):
    """
    Resta el argumento al valor.
    Uso: {{ total_cupos|subtract:inscritos }}
    """
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        # Intento secundario con float/decimal si falla int
        try:
            return float(value) - float(arg)
        except (ValueError, TypeError):
            return 0


@register.filter(name='to_str')
def to_str(value):
    """
    Convierte cualquier valor a cadena de texto.
    VITAL para comparaciones de UUIDs en templates.
    
    Uso: {% if objeto.id|to_str == otro_id|to_str %}
    """
    return str(value) if value is not None else ""