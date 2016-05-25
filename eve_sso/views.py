from __future__ import unicode_literals

import urllib
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.utils.six import string_types
from django.utils.six.moves.urllib.parse import urlparse, urlunparse
from django.core.urlresolvers import reverse
from django.http import QueryDict
from eve_sso.models import CallbackCode, CallbackRedirect

EVE_SSO_LOGIN_URL = "https://login.eveonline.com/oauth/authorize/"

def sso_redirect(request, scopes=[]):
    """
    Generates a :model:`eve_sso.CallbackRedirect` for the specified request.
    Redirects to EVE for login.
    """
    if isinstance(scopes, string_types):
        scopes = scopes.split()
    scope_querystring = ' '.join(scopes)

    params = {
        'response_type': 'code',
        'redirect_uri': settings.EVE_SSO_CALLBACK_URL,
        'client_id': settings.EVE_SSO_CLIENT_ID,
        'scope': scope_querystring,
    }

    # ensure only one callback redirect model per session
    CallbackRedirect.objects.filter(session_key=request.session.session_key).delete()

    # ensure session installed in database    
    if not request.session.exists(request.session.session_key):
        request.session.create()

    model = CallbackRedirect.objects.create(session_key=request.session.session_key, url=request.get_full_path())

    params['state'] = model.hash_string
    param_string = urllib.urlencode(params)
    return redirect(EVE_SSO_LOGIN_URL + '?' + param_string)

def receive_callback(request):
    """
    Parses SSO callback, validates, retrieves :model:`eve_sso.AccessToken`, and
    internally redirects to the target url.
    """
    code = request.GET.get('code', None)
    state = request.GET.get('state', None)
    model = get_object_or_404(CallbackRedirect, hash_string=state)
    if model.validate(request):
        cc = CallbackCode.objects.create(code=code)
        token = cc.exchange()
        try:
            token.user = request.user
            token.save()
        except ValueError:
            # user is not logged in
            pass
        model.token = token
        model.save()
    return redirect(model.url)
