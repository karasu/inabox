""" This token can be used to verify a user through email. """

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from six import text_type

class TokenGenerator(PasswordResetTokenGenerator):
    """ Creates a hash from user id and timespan """
    def _make_hash_value(self, user, timestamp):
        return (
            text_type(user.pk) + text_type(timestamp) +
            text_type(user.profile.email_is_verified)
        )

account_activation_token = TokenGenerator()
