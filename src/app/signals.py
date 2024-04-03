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
        # Create user's profile
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    """ run after a user is saved """
    # Save user's profile
    instance.profile.save()

    # Also store user (sender) and profile to LDAP
    print("-- sender:", sender)
    print("-- instance:", instance)
    print("-- kwargs:", *kwargs)

    #instance.save(using="ldap")
    #instance.save(using="ldap", force_insert=True)
    #sender.save(using="ldap", force_insert=True)
    #instance.profile.save(using="ldap", force_insert=True)


# (receiver, receiver(signal=self, sender=sender, **named))