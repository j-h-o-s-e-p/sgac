from django import template
import json

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Permite acceder a valores de un diccionario usando una key dinámica.
    Maneja conversión automática entre UUID/String/Int.
    Uso: {{ mi_dict|get_item:variable_key }}
    """
    # 1. Validación básica
    if dictionary is None:
        return None

    # 2. Soporte para strings JSON (por si acaso viene serializado)
    if isinstance(dictionary, str):
        try:
            dictionary = json.loads(dictionary)
        except (ValueError, TypeError):
            return None

    # 3. Asegurar que sea diccionario
    if not isinstance(dictionary, dict):
        return None

    # 4. Estrategia de búsqueda en cascada (La "magia" para que no falle)
    
    # Intento A: Coincidencia exacta (la más rápida)
    if key in dictionary:
        return dictionary[key]
    
    # Intento B: Convertir key a String (Vital para UUIDs vs Strings)
    key_str = str(key)
    if key_str in dictionary:
        return dictionary[key_str]
    
    # Intento C: Convertir key a Entero (Si parece número)
    if key_str.isdigit():
        try:
            key_int = int(key_str)
            if key_int in dictionary:
                return dictionary[key_int]
        except (ValueError, TypeError):
            pass
            
    return None


@register.filter(name='subtract')
def subtract(value, arg):
    """
    Resta el argumento al valor.
    Uso: {{ total|subtract:usados }}
    """
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return 0