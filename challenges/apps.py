""" Define Challenge main class """

from django.apps import AppConfig

from .logger import setup_logger

class ChallengesConfig(AppConfig):
    """ Challenges app class """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'challenges'
    verbose_name = "Challenges"

    def ready(self):
        """ startup code goes here """
        setup_logger()
