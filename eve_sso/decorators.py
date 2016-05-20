from functools import wraps
from django.utils.decorators import available_attrs
from django.utils.six.moves.urllib.parse import urlparse, urlunparse
from django.core.urlresolvers import reverse
from django.http import QueryDict
from django.shortcuts import redirect
from eve_sso.models import AccessToken, Scope, TokenError

def scopes_required(scopes):
    """
    Decorator for views that returns an AccessToken
    for the user with required scopes.
    Takes a list of strings of scope names.
    """
    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            scope_models = set([])
            if isinstance(scopes, basestring):
                scope_models.add(Scope.objects.get(name=scopes))
            else:
                for s in scopes:
                    scopes_models.add(Scope.objects.get(name=s))
            for t in AccessToken.objects.filter(user=request.user).filter(scopes__contains=scopes_models):
                try:
                    t.token
                    return view_func(request, t, *args, **kwargs)
                except TokenError:
                    t.delete()
            sso_url_parts = urlparse(reverse('eve_sso:redirect'))
            querystring = QueryDict(sso_url_parts[4], mutable=True)
            querystring['next'] = reverse(view_func)
            sso_url_parts[4] = querystring.urlencode(safe='/')
            return redirect(urlunparse(sso_url_parts))
        return _wrapped_view
    return decorator
