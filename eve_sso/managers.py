from __future__ import unicode_literals
from django.db import models
import json

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
        salt = kwargs.pop('salt', None)
        hash_string = kwargs.pop('hash_string', None)
        model = self.model()
        if not salt:
            salt = model.generate_salt()
        if not hash_string:
            hash_string = model.generate_hash(session_key, salt)
        check_hash = model.generate_hash(session_key, salt)
        if check_hash != hash_string:
            raise ValueError("Hash string does not match provided salt and session key.")
        return super(CallbackRedirectManager, self).create(session_key=session_key, salt=salt, hash_string=hash_string, *args, **kwargs)

    def create_by_request(self, request):
        """
        Shortcut function to create model based on a request object.
        """
        if not request.session.exists(request.session.session_key):
            # install session in database
            request.session.create()
        get = dict(request.GET)
        url = get('return', '/')
        get = json.dumps(get)
        return super(CallbackRedirectManager, self).create(session_key=request.session.session_key, url=url, get=get)

    def get_by_request(self, request):
        """
        Shortcut function to get model based on a request object.
        """
        if not request.session.exists(request.session.session_key):
            # install session in database
            request.session.create()
        return super(CallbackRedirectManager, self).get(session_key=request.session.session_key)

class AccessTokenManager(models.Manager):
    """
    Provides additional functionality for creating :model:`eve_sso.AccessToken` instances.
    """
    def create_from_json(dict):
        """
        Reads the returned json data from exchanging a SSO :model:`CallbackCode` and creates a model.
        """
        access_token = dict['access_token']
        token_type = dict['token_type']
        refresh_token = dict['refresh_token']
        return super(AccessTokenManager, self).create(access_token=access_token, token_type=token_type, refresh_token=refresh_token)
