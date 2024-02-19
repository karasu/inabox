""" Define Challenge main class """

from django.apps import AppConfig

from .logger import setup_logger

class InaboxConfig(AppConfig):
    """ App app class """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        """ startup code goes here """
        setup_logger()
