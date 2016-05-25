from __future__ import unicode_literals
from django.db import models

class CallbackRedirectManager(models.Manager):
    """
    Provides additional functionality for creating and retrieving :model:`eve_sso.CallbackRedirect` instances.
    """
    def create(self, *args, **kwargs):
        """
        Generates requisite salt and hash string for model creation.
        Validates any provided session key, salt, and hash string match.
        """
        session_key = kwargs['session_key']
        model = self.model()
        try:
            salt = kwargs.pop('salt', [None])[0]
            assert salt
        except (KeyError, AssertionError):
            salt = model.generate_salt()
        try:
           hash_string = kwargs.pop('hash_string', [None])[0]
           assert hash_string
        except (KeyError, AssertionError):
            hash_string = model.generate_hash(session_key, salt)
        assert hash_string == model.generate_hash(session_key, salt)
        return super(CallbackRedirectManager, self).create(salt=salt, hash_string=hash_string, *args, **kwargs)
