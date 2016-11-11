from __future__ import unicode_literals
from base64 import b64encode
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django_settingsdict import SettingsDict

REQUIRED = (
    # Create application id and secret on https://developers.eveonline.com/applications
    'CLIENT_ID',     # EVE 3rd party application id
    'CLIENT_SECRET', # EVE 3rd partu application secret
    'CALLBACK_URL',  # return path from eve login to 3rd party application
)

DEFAULTS = {
    # Scopes used for login
    'LOGIN_SCOPES': [],
    # Create unknown users if no user is found
    'AUTH_CREATE_UNKNOWN_USER': True,
    # function that creates user: called with token as only parameter
    'AUTH_USER_FROM_TOKEN_FUNC': None,
    # function that finds user using the token. if none
    'AUTH_FIND_USER_FUNC': None, # function that
    # Field that contains redirect target from login page
    'REDIRECT_FIELD_NAME': REDIRECT_FIELD_NAME,

    # Different urls and paths used in authentication
    'LOGIN_URL': "https://login.eveonline.com/oauth/authorize/",
    'CODE_EXCHANGE_URL': "https://login.eveonline.com/oauth/token",
    'CODE_EXCHANGE_GRANT_TYPE': 'authorization_code',
    'TOKEN_REFRESH_URL': "https://login.eveonline.com/oauth/token",
    'TOKEN_REFRESH_GRANT_TYPE': 'refresh_token',
    'TOKEN_VERIFY_URL': "https://login.eveonline.com/oauth/verify",
    # If characters account (owner) has changed, purge that token
    'PURGE_TOKENS_ON_ACCOUNT_CHANGE': True,
    # You can set shorter valid duration than what CREST states
    'TOKEN_VALID_DURATION': None,

    # Some extra paths
    'PORTRAIT_URL_TEMPLATE': "//image.eveonline.com/Character/{charid}_{size}.jpg",

    # Different error messages
    'MESSAGE_INVALID_REQUEST': _('Invalid query parameters for request'),
    'MESSAGE_INVALID_CALLBACK': _("This login information is not valid anymore. Try login in again."),
    'MESSAGE_ACCOUNT_INACTIVE': _("User account disabled"),
    'MESSAGE_ACCOUNT_NOT_REGISTERED': _("No account found with provided token"),
}

IMPORT_STRINGS = (
    'AUTH_USER_FROM_TOKEN_FUNC',
    'AUTH_FIND_USER_FUNC',
)


class EveSsoSettings(SettingsDict):
    @cached_property
    def AUTH_TOKEN(self):
        token = "{}:{}".format(self.CLIENT_ID, self.CLIENT_SECRET)
        auth = b64encode(token.encode('utf-8')).decode('utf-8')
        return "Basic {}".format(auth)


app_settings = EveSsoSettings('EVE_SSO',
                              required=REQUIRED,
                              defaults=DEFAULTS,
                              import_strings=IMPORT_STRINGS)
