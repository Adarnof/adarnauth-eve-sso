from __future__ import unicode_literals

import logging

try:
    from urllib import urlencode
    from urlparse import urljoin
except ImportError: #py3
    from urllib.parse import urlencode, urljoin

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseForbidden, HttpResponseBadRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.six import string_types
from django.views.decorators.http import require_http_methods

from .app_settings import app_settings
from .models import CallbackRedirect, AccessToken


logger = logging.getLogger('eve_sso.views')


def sso_redirect(request, scopes=None, return_to=None, allow_authentication=False):
    """
    Generates a :model:`eve_sso.CallbackRedirect` for the specified request.
    Redirects to EVE for login.
    Accepts a view or URL name as a redirect after SSO.
    """
    if isinstance(scopes, string_types):
        scopes = scopes.split()

    # ensure session is installed in database
    session = request.session
    if not session.exists(session.session_key):
        session.create()

    url = return_to or request.get_full_path()
    model = CallbackRedirect.objects.create(
        session_key=session.session_key,
        allow_authentication=allow_authentication,
        url=url)

    params = '?'+urlencode({
        'response_type': 'code',
        'redirect_uri': app_settings.CALLBACK_URL,
        'client_id': app_settings.CLIENT_ID,
        'scope': ' '.join(scopes or []),
        'state': model.hash_string,
    })
    return redirect(urljoin(app_settings.LOGIN_URL, params))


@require_http_methods(['GET'])
def receive_callback(request):
    """
    Parses SSO callback, validates, retrieves :model:`eve_sso.AccessToken`, and
    internally redirects to the target url.
    """
    code = request.GET.get('code', None)
    state = request.GET.get('state', None)

    # Validate request
    if not code or not state:
        return HttpResponseBadRequest(app_settings.MESSAGE_INVALID_REQUEST)
    model = CallbackRedirect.objects.get_or_none(hash_string=state)
    if not model or not model.validate(request):
        logger.warning("CallbackRedirect not valid for request with session key '%s', state '%s' and model %r", request.session.session_key, state, model)
        raise HttpResponseForbidden(app_settings.MESSAGE_INVALID_CALLBACK)

    # FIXME: django 2.0 doesn't support calling
    user = request.user if request.user.is_authenticated() else None

    # Resolve token from model or from code and store in model
    if model.token:
        token = model.token
        logger.debug("receive_callback: Using token from redirect model: %r", token)
    else:
        token = AccessToken.objects.get_or_create_from_code(code, owner=user)
        model.token = token
        model.save(update_fields=['token'])
        logger.debug("receive_callback: Resolved token from code: %r", token)

    # Do authentication for token if it's allowed
    if not user and model.allow_authentication:
        # Authenticate the user
        user = authenticate(crest_token=token)

        # Validate the user
        if not user:
            return HttpResponseForbidden(app_settings.MESSAGE_ACCOUNT_NOT_REGISTERED)
        if not user.is_active:
            return HttpResponseForbidden(app_settings.MESSAGE_ACCOUNT_INACTIVE)

        # log the user in
        login(request, user)

        # This was only login token, so it can be removed now
        if not token.can_refresh:
            token.delete() # Will remove CallbackRedirect too

    # Check that not bad things happen
    elif user and user != token.owner:
        logger.critical("Token doesn't have logged in user as owner: token=%r, user=%r", token, user)
        raise RuntimeError(
            "BUG: For some reason we got token with different owner than "
            "the current logged in user. This shouldn't ever happen. "
            "Please file bug report in the project issue tracker."
        )

    # When everything is ok, redirect
    return redirect(model.url)


def login_view(request):
    """
    EVE SSO login redirect view.
    Will forward to EVE SSO login page (using sso_redirect()) if user is not logged in.
    Sets return path to LOGIN_REDIRECT_URL or one in query parameter.
    """
    return_to = request.GET.get(app_settings.REDIRECT_FIELD_NAME, None) \
        or settings.LOGIN_REDIRECT_URL

    # FIXME: django 2.0 doesn't support calling
    if request.user.is_authenticated():
        return redirect(return_to)

    return sso_redirect(request,
                        scopes=app_settings.LOGIN_SCOPES,
                        return_to=return_to,
                        allow_authentication=True)
