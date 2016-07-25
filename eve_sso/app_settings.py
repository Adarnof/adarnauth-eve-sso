from django.conf import settings

EVE_SSO_CLIENT_ID = getattr(settings, 'EVE_SSO_CLIENT_ID')
EVE_SSO_CLIENT_SECRET = getattr(settings, 'EVE_SSO_CLIENT_SECRET')
EVE_SSO_CALLBACK_URL = getattr(settings, 'EVE_SSO_CALLBACK_URL')
EVE_SSO_TOKEN_VALID_DURATION = getattr(settings, 'EVE_SSO_TOKEN_VALID_DURATION', 1200)
