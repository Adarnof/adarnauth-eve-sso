from __future__ import unicode_literals

import urllib
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from eve_sso.models import AccessToken, CallbackCode, CallbackRedirect

def sso_redirect(request):
    """
    Generates a :model:`eve_sso.CallbackRedirect` for the specified request.
    Redirects to EVE for login.
    """
    EVE_SSO_LOGIN_URL = "https://login.eveonline.com/oauth/authorize/"
    params = {
        'response_type': 'code',
        'redirect_uri': settings.EVE_SSO_CALLBACK_URI,
        'client_id': settings.EVE_SSO_CLIENT_ID,
        'scope': request.GET.get('scope', ''),
    }
    # ensure only one callback redirect model
    try:
        CallbackRedirect.objects.get_by_request(request).delete()
    except CallbackRedirect.DoesNotExist:
        pass
    model = CallbackRedirect.objects.create_by_request(request)
    params['state'] = model.hash_string
    param_string = urllib.urlencode(params)
    return redirect(EVE_SSO_LOGIN_URL + '?' + param_string)

def receive_callback(request):
    """
    Parses SSO callback, validates, retrieves :model:`eve_sso.AccessToken`, and internally redirects.
    """
    code = request.GET.get('code', None)
    state = request.GET.get('state', None)
    model = get_object_or_404(CallbackRedirect, hash_string=state)
    if model.validate(request):
        cc = CallbackCode.objects.create(code=code)
        token = cc.exchange()
        model.token = token
        model.save()
        return redirect(model.url)
    else:
        return redirect(eve_sso.views.sso_redirect)
