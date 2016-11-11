from __future__ import unicode_literals
from base64 import b64encode
from django.utils.functional import cached_property
from django_settingsdict import SettingsDict

REQUIRED = (
    # Create application id and secret on https://developers.eveonline.com/applications
    'CLIENT_ID',     # EVE 3rd party application id
    'CLIENT_SECRET', # EVE 3rd partu application secret
    'CALLBACK_URL',  # return path from eve login to 3rd party application
)

DEFAULTS = {
    # Different urls and paths used in authentication
    'LOGIN_URL': "https://login.eveonline.com/oauth/authorize/",
    # You can set shorter valid duration than what CREST states
    'TOKEN_VALID_DURATION': None,
}

IMPORT_STRINGS = (
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


# Backwards compatibility
EVE_SSO_CLIENT_ID = app_settings.CLIENT_ID
EVE_SSO_CLIENT_SECRET = app_settings.CLIENT_SECRET
EVE_SSO_CALLBACK_URL = app_settings.CALLBACK_URL
EVE_SSO_TOKEN_VALID_DURATION = app_settings.TOKEN_VALID_DURATION
