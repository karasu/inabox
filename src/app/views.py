""" app views go here """

from views import *

@register.filter
def get_item(dictionary, key):
    """ Filter to get dict item in a loop """
    return dictionary.get(key)
