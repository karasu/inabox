""" Template tags """
from django.template.defaulttags import register

@register.filter
def get_item(dictionary, key):
    """ Filter to get dict item in a loop """
    return dictionary.get(key)
