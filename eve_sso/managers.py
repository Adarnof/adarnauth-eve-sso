from __future__ import unicode_literals
import logging
from django.db import models


logger = logging.getLogger('eve_sso.managers')


class CallbackRedirectManager(models.Manager):
    """
    Provides additional functionality for creating and retrieving
    :model:`eve_sso.CallbackRedirect` instances.
    """

    def create(self, session_key, **kwargs):
        """
        Generates requisite salt and hash string for model creation.
        Validates any provided session key, salt, and hash string match.
        """
        model = self.model
        salt = kwargs.pop('salt', None) or model.generate_salt()
        generated_hash_string = model.generate_hash(session_key, salt)
        hash_string = kwargs.pop('hash_string', generated_hash_string)
        if hash_string != generated_hash_string:
            raise ValueError("Value for `hash_string` is invalid. Leave blank or use .generate_hash(()")

        return super(CallbackRedirectManager, self).create(
            salt=salt,
            hash_string=hash_string,
            session_key=session_key,
            **kwargs)
