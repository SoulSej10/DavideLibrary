# library/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter(name='obfuscate')
def obfuscate(value):
    """Obfuscate the input value with asterisks."""
    return '*' * len(value)
