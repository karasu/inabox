""" Signals file.
Signals are used to perform some action on modification/creation
of a particular entry in database. """

from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **_kwargs):
    """ is run every time a user is created """ 
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_profile(sender, instance, **_kwargs):
    """ run after a user is saved """
    instance.profile.save()
    # Also store user (sender) and profile to LDAP
    sender.save(using="ldap", force_insert=True)
    instance.profile.save(using="ldap", force_insert=True)
