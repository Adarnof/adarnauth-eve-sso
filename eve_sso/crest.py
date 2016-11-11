import logging
import requests
from collections import namedtuple
from datetime import timedelta
from django.utils import timezone

from .app_settings import app_settings


logger = logging.getLogger('eve_sso.crest')


class CrestError(Exception):
    pass

class InvalidAuthentication(CrestError):
    pass


class TokenError(Exception):
    pass


class TokenInvalidError(TokenError):
    pass


class TokenExpiredError(TokenError):
    pass


class NotRefreshableTokenError(TokenError):
    pass


class TokenResponse(namedtuple('TokenResponse', (
    'type',
    'access_token',
    'refresh_token',
    'updated',
    'expires',
))):
    @classmethod
    def from_json(cls, json):
        # Expiration time
        expires_in = json['expires_in']
        valid = app_settings.TOKEN_VALID_DURATION
        expires = timedelta(seconds=min(expires_in, valid) if valid else expires_in)
        now = timezone.now()

        return cls(
            json['token_type'],
            json['access_token'],
            json['refresh_token'],
            now,
            now + expires,
        )


class VerifyResponse(namedtuple('VerifyResponse', (
    'token_type',
    'character_id',
    'character_name',
    'character_owner_hash',
    'expires_on',
    'scopes',
))):
    @classmethod
    def from_json(cls, json):
        return cls(
            json['TokenType'],
            json['CharacterID'],
            json['CharacterName'],
            json['CharacterOwnerHash'],
            json['ExpiresOn'],
            frozenset(json.get('Scopes', '').split()),
        )


# FIXME: handle timeouts

class CrestTokenAPI(object):
    """
    Simple crest api interface for token refresh and verification.
    For other crest actions PyCrest could be used.
    """

    @staticmethod
    def get_session():
        return requests.Session()


    def __init__(self, session=None):
        self.session = session or self.get_session()

    def verify_authorization_code(self, code):
        headers = {'Authorization': app_settings.AUTH_TOKEN}
        r = self.session.post(
            app_settings.CODE_EXCHANGE_URL,
            headers=headers,
            data={
                'grant_type': app_settings.CODE_EXCHANGE_GRANT_TYPE,
                'code': code,
            })
        if r.status_code in (400, 401):
            raise InvalidAuthentication(
                "Crest didn't accept our authentication code. Got {}: {}"
                .format(r.status_code, r.text)
            )
        r.raise_for_status()
        return TokenResponse.from_json(r.json())

    def verify_token(self, access_token):
        headers = {'Authorization': "Bearer {}".format(access_token)}
        r = self.session.get(app_settings.TOKEN_VERIFY_URL, headers=headers)
        if r.status_code in (400, 401, 403):
            logger.warning("TokenInvalidError: refresh_token failed with %s: %s", r.status_code, r.text)
            raise TokenInvalidError()
        r.raise_for_status()
        return VerifyResponse.from_json(r.json())

    def refresh_token(self, refresh_token):
        headers = {'Authorization': app_settings.AUTH_TOKEN}
        r = self.session.post(
            app_settings.TOKEN_REFRESH_URL,
            headers=headers,
            data={
                'grant_type': app_settings.TOKEN_REFRESH_GRANT_TYPE,
                'refresh_token': refresh_token,
            })
        if r.status_code in (400, 401):
            raise InvalidAuthentication(
                "Crest didn't accept our authentication code. Got {}: {}"
                .format(r.status_code, r.text)
            )
        if r.status_code == 403:
            logger.warning("TokenInvalidError: refresh_token failed with %s: %s", r.status_code, r.text)
            raise TokenInvalidError
        r.raise_for_status()
        return TokenResponse.from_json(r.json())
