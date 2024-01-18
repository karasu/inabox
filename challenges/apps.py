""" Define Challenge main class """

from django.apps import AppConfig


class ChallengesConfig(AppConfig):
    """ Challenges app class """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'challenges'
