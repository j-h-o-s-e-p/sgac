from django import template
import json

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Permite acceder a elementos de un diccionario o JSON usando una variable como key.
    Uso: {{ my_dict|get_item:my_key }}
    """

    if dictionary is None:
        return None

    # Si viene como string, intenta convertirlo a dict
    if isinstance(dictionary, str):
        try:
            dictionary = json.loads(dictionary)
        except json.JSONDecodeError:
            return None

    # Si no es dict después de procesar, salir
    if not isinstance(dictionary, dict):
        return None

    # Convertir key a entero si es numérico (tu lógica original)
    try:
        key = int(key) if str(key).isdigit() else key
    except ValueError:
        pass

    return dictionary.get(key)
