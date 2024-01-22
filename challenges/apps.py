""" Define Challenge main class """

from django.apps import AppConfig

from .task_switchbox import switchbox_task

class ChallengesConfig(AppConfig):
    """ Challenges app class """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'challenges'
    verbose_name = "Challenges"
    res = None

    def ready(self):
        """ startup code goes here """
        self.res = switchbox_task.delay()
