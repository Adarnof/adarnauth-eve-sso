from functools import wraps
from django.utils.decorators import available_attrs
from django.utils.six import string_types
from eve_sso.models import AccessToken, CallbackRedirect, Scope, TokenError


import logging

logger = logging.getLogger(__name__)

def token_required(scopes=[], new=False):
    """
    Decorator for views to request an AccessToken.
    Accepts required scopes as a space-delimited string
    or list of strings of scope names.
    Can require a new token to be retrieved by SSO.
    Returns a QueryDict of AccessTokens.
    """

    # support single string scopes
    if isinstance(scopes, string_types):
        scopes = scopes.split()

    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            # ensure session installed in database
            if not request.session.exists(request.session.session_key):
                request.session.create()

            # clean up callback redirect, pass token if new requested
            try:
                model = CallbackRedirect.objects.get(session_key=request.session.session_key)
                tokens = AccessToken.objects.filter(pk=model.token.pk)
                model.delete()
                if new:
                    return view_func(request, tokens, *args, **kwargs)
            except (CallbackRedirect.DoesNotExist, AttributeError):
                pass

            if not new:
                # ensure user logged in to check existing tokens
                if not request.user.is_authenticated():
                    from django.contrib.auth.views import redirect_to_login
                    return redirect_to_login(request.get_full_path())

                # collect tokens in db, check if still valid, return if any
                for t in AccessToken.objects.filter(user__pk=request.user.pk).filter(scopes__name__in=scopes):
                    try:
                        t.token
                    except TokenError:
                        t.delete()
                tokens = AccessToken.objects.filter(user__pk=request.user.pk).filter(scopes__name__in=scopes)
                if tokens.exists():
                    return view_func(request, tokens, *args, **kwargs)

            # trigger creation of new token via sso
            from eve_sso.views import sso_redirect
            return sso_redirect(request, scopes=scopes)
        return _wrapped_view
    return decorator
