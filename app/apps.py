""" Define Challenge main class """

from django.apps import AppConfig

from .logger import setup_logger

class InaboxAppConfig(AppConfig):
    """ App app class """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        """ startup code goes here """
        setup_logger()
