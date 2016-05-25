from __future__ import unicode_literals
from django.db import models
from django.utils.six.moves.urllib.parse import urlparse, urlunparse
from django.http import QueryDict

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
        except KeyError:
            salt = model.generate_salt()
        try:
           hash_string = kwargs.pop('hash_string', [None])[0]
        except KeyError:
            hash_string = model.generate_hash(session_key, salt)
        assert hash_string == model.generate_hash(session_key, salt)
        return super(CallbackRedirectManager, self).create(session_key=session_key, salt=salt, hash_string=hash_string, *args, **kwargs)

    def create_by_request(self, request):
        """
        Shortcut function to create model based on a request object.
        """
        if not request.session.exists(request.session.session_key):
            # install session in database
            request.session.create()
        path = request.get_full_path()
        path_parts = urlparse(path)
        get_dict = QueryDict(path_parts[4], mutable=True)
        # remove scopes, if any
        get_dict.pop('scope', None)
        # build target url
        url = get_dict.pop('redirect', ['/'])[0]
        url_parts = list(urlparse(url))
        url_parts[4] = get_dict.urlencode(safe='/')
        url = urlunparse(url_parts)
        return super(CallbackRedirectManager, self).create(session_key=request.session.session_key, url=url)

    def get_by_request(self, request):
        """
        Shortcut function to get model based on a request object.
        """
        if not request.session.exists(request.session.session_key):
            # install session in database
            request.session.create()
        return super(CallbackRedirectManager, self).get(session_key=request.session.session_key)
