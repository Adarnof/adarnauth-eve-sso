from __future__ import unicode_literals
from django.utils.encoding import python_2_unicode_compatible
from django.db import models
from django.conf import settings
from eve_sso.app_settings import EVE_SSO_CLIENT_ID, EVE_SSO_CLIENT_SECRET, EVE_SSO_TOKEN_VALID_DURATION
import requests
from django.utils import timezone
import base64
import uuid
import hashlib
import datetime
from eve_sso.managers import CallbackRedirectManager


class TokenError(Exception):
    pass


class TokenInvalidError(TokenError):
    pass


class TokenExpiredError(TokenError):
    pass


class NotRefreshableTokenError(TokenError):
    pass


def generate_auth_string():
    client_id = EVE_SSO_CLIENT_ID
    client_secret = EVE_SSO_CLIENT_SECRET
    conc = "%s:%s" % (client_id, client_secret)
    auth = base64.b64encode(conc.encode('utf-8'))
    return 'Basic ' + auth.decode(encoding='utf-8')


@python_2_unicode_compatible
class Scope(models.Model):
    """
    Represents an access scope granted by SSO.
    """
    name = models.CharField(max_length=100, unique=True, help_text="The official EVE name fot the scope.")
    help_text = models.TextField(help_text="The official EVE description of the scope.")

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class CallbackCode(models.Model):
    """
    Stores the code received from SSO callback.
    """
    CODE_EXCHANGE_URL = "https://login.eveonline.com/oauth/token"
    TOKEN_EXCHANGE_URL = "https://login.eveonline.com/oauth/verify"

    code = models.CharField(max_length=254, help_text="Code used to retrieve access token from SSO.")
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code

    def exchange(self):
        """
        Exchanges SSO callback code for access token. Returns :model:`eve_sso.AccessToken`. Self-deletes.
        """
        custom_headers = {
            'Authorization': generate_auth_string(),
            'Content-Type': 'application/json',
        }
        data = {
            'grant_type': 'authorization_code',
            'code': self.code,
        }
        r = requests.post(self.CODE_EXCHANGE_URL, headers=custom_headers, json=data)
        r.raise_for_status()
        access_token = r.json()['access_token']
        refresh_token = r.json()['refresh_token']

        custom_headers = {'Authorization': 'Bearer ' + access_token}

        r = requests.get(self.TOKEN_EXCHANGE_URL, headers=custom_headers)
        if r.status_code == 403:
            raise TokenInvalidError()
        r.raise_for_status()
        model = AccessToken.objects.create(
            character_id=r.json()['CharacterID'],
            character_name=r.json()['CharacterName'],
            character_owner_hash=r.json()['CharacterOwnerHash'],
            access_token=access_token,
            refresh_token=refresh_token,
            token_type=r.json()['TokenType']
        )

        if 'Scopes' in r.json():
            for s in r.json()['Scopes'].split():
                scope = Scope.objects.get(name=s)
                model.scopes.add(scope)

        self.delete()
        return model


@python_2_unicode_compatible
class AccessToken(models.Model):
    """
    Stores the token returned by SSO callback.
    """
    TOKEN_REFRESH_URL = "https://login.eveonline.com/oauth/token"
    TOKEN_REFRESH_GRANT_TYPE = 'refresh_token'

    created = models.DateTimeField(auto_now_add=True)
    access_token = models.CharField(max_length=254, unique=True, help_text="The access token granted by SSO.")
    refresh_token = models.CharField(max_length=254, blank=True, null=True,
                                     help_text="A re-usable token to generate new access tokens upon expiry. "
                                               "Only applies when scopes are granted by SSO.")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True,
                             help_text="The user to whom this token belongs.")
    character_id = models.IntegerField(help_text="The ID of the EVE character who authenticated by SSO.")
    character_name = models.CharField(max_length=100,
                                      help_text="The name of the EVE character who authenticated by SSO.")
    token_type = models.CharField(max_length=100, choices=(('Character', 'Character'), ('Corporation', 'Corporation'),),
                                  default='Character', help_text="The applicable range of the token.")
    character_owner_hash = models.CharField(max_length=254,
                                            help_text="The unique string identifying this character and its owning EVE "
                                                      "account. Changes if the owning account changes.")
    scopes = models.ManyToManyField(Scope, blank=True, help_text="The access scopes granted by this SSO token.")

    def __str__(self):
        return "%s - %s" % (self.character_name, ", ".join([s.name for s in self.scopes.all()]))

    @property
    def can_refresh(self):
        """
        Determines if this token can be refreshed upon expiry
        """
        if self.refresh_token:
            return True
        else:
            return False

    @property
    def expired(self):
        """
        Determines if the access token has expired.
        """
        if self.created + datetime.timedelta(seconds=EVE_SSO_TOKEN_VALID_DURATION) > timezone.now():
            return False
        else:
            return True

    @property
    def token(self):
        """
        Returns the access token. If expired, automatically refreshes.
        """
        if self.expired:
            if self.can_refresh:
                self.refresh()
            else:
                raise TokenExpiredError()
        return self.access_token

    def refresh(self):
        """
        Exchanges refresh token to generate a fresh access token.
        """
        if self.can_refresh:
            custom_headers = {
                'Content-Type': 'application/json',
                'Authorization': generate_auth_string(),
            }
            params = {
                'grant_type': self.TOKEN_REFRESH_GRANT_TYPE,
                'refresh_token': self.refresh_token,
            }
            r = requests.post(self.TOKEN_REFRESH_URL, params=params, headers=custom_headers)
            if r.status_code in [400, 403]:
                raise TokenInvalidError()
            r.raise_for_status()
            self.created = timezone.now()
            self.access_token = r.json()['access_token']
            self.save()
        else:
            raise NotRefreshableTokenError()


@python_2_unicode_compatible
class CallbackRedirect(models.Model):
    """
    Records the intended destination for the SSO callback.
    Used to internally redirect SSO callbacks.
    """
    salt = models.CharField(max_length=32, help_text="Cryptographic salt used to generate the hash string.")
    hash_string = models.CharField(max_length=128, help_text="Cryptographic hash used to reference this callback.")
    url = models.CharField(max_length=254, default='/', help_text="The internal URL to redirect this callback towards.")
    session_key = models.CharField(max_length=254, unique=True,
                                   help_text="Session key identifying session this redirect was created for.")
    created = models.DateTimeField(auto_now_add=True)
    token = models.ForeignKey(AccessToken, blank=True, null=True,
                              help_text="AccessToken generated by a completed code exchange from callback processing.")

    objects = CallbackRedirectManager()

    def __str__(self):
        return "Redirect for %s to url %s" % (self.session_key, self.url)

    @staticmethod
    def generate_hash(session_key, salt):
        """
        Generate the hash string comprised of the provided session key and salt.
        """
        session_key = str(session_key).encode('utf-8')
        salt = str(salt).encode('utf-8')
        return hashlib.sha512(session_key + salt).hexdigest()

    @staticmethod
    def generate_salt():
        """
        Produce a random salt to be used for hashing.
        """
        return uuid.uuid4().hex

    def validate(self, request):
        """
        Verify the given request is associated with this redirect.
        """
        if not self.hash_string or not self.salt:
            raise AttributeError("Model is not yet populated.")
        if not request.session.exists(request.session.session_key):
            # install session in database
            request.session.create()
        req_hash = self.generate_hash(request.session.session_key, self.salt)
        state = request.GET.get('state', None)
        if req_hash == state:
            # ensures state is a match for the request session
            if req_hash == self.hash_string:
                # ensures the request session is a match for this redirect
                return True
        return False
