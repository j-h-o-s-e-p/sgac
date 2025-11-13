from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Permite acceder a elementos de un diccionario usando una variable como key
    Uso: {{ my_dict|get_item:my_key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(int(key) if str(key).isdigit() else key)