from functools import wraps
from django.utils.decorators import available_attrs
from django.utils.six.moves.urllib.parse import urlparse, urlunparse
from django.core.urlresolvers import reverse
from django.http import QueryDict
from django.shortcuts import redirect
from eve_sso.models import AccessToken, CallbackRedirect, Scope, TokenError

def token_required(scopes=[]):
    """
    Decorator for views to request a new AccessToken.
    Takes an optional list of scope names.
    Returns a new token as a QuerySet.
    """
    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            try:
                model = CallbackRedirect.objects.get_by_request(request)
                tokens = AccessToken.objects.filter(pk=model.token.pk)
                model.delete()
                return view_func(request, tokens, *args, **kwargs)
            except CallbackRedirect.DoesNotExist:
                if isinstance(scopes, basestring):
                    scope_querystring = scopes
                else:
                    scope_querystring = str.join(' ', scopes)
                incoming_url_parts = urlparse(request.get_full_path())
                sso_url_parts = urlparse(reverse('eve_sso:redirect'))
                querystring = QueryDict(incoming_url_parts[4], mutable=True)
                querystring['redirect'] = incoming_url_parts[2]
                querystring['scope'] = scope_querystring
                sso_url_parts[4] = querystring.urlencode(safe='/')
                return redirect(urlunparse(sso_url_parts))
        return _wrapped_view
    return decorator

def scopes_required(scopes):
    """
    Decorator for views that returns an AccessToken
    for the user with required scopes.
    Takes a list of strings of scope names.
    Returns a QuerySet of tokens matching the query.
    """
    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            scope_models = set([])
            if isinstance(scopes, basestring):
                scope_models.add(Scope.objects.get(name=scopes))
                scope_querystring = scopes
            else:
                for s in scopes:
                    scopes_models.add(Scope.objects.get(name=s))
                scope_querystring = str.join(' ', scopes)
            for t in AccessToken.objects.filter(user=request.user).filter(scopes__contains=scopes_models):
                # make sure tokens on file are still valid
                try:
                    t.token
                except TokenError:
                    t.delete()
            tokens = AccessToken.objects.filter(user=request.user).filter(scopes__contains=scopes_models):
            if tokens.exists():
                return tokens
            else:
                return token_required(scopes=scopes)
        return _wrapped_view
    return decorator
