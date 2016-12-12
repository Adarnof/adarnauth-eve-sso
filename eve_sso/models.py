from __future__ import unicode_literals
import hashlib
import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _

from .app_settings import app_settings
from .managers import AccessTokenManager, CallbackRedirectManager
from .crest import (
    TokenInvalidError,
    TokenExpiredError,
    NotRefreshableTokenError,
    CrestTokenAPI,
)


@python_2_unicode_compatible
class PortraitUrl(object):
    """
    Take character_id and renders url to EVE image server when converted to
    string or called. Different sizes can be selected using argument to
    __call__ or via __getitem__ (for django templates).
    """
    def __init__(self, character_id):
        self.character_id = character_id

    def get_portrait_url(self, size=None):
        """
        Returns URL to Character portrait from EVE Image Server
        Not all sizes are valid. Some known: 32, 50, 64, 128, 256, 512
        Read https://image.eveonline.com/
        """
        return app_settings.PORTRAIT_URL_TEMPLATE.format(
            charid=self.character_id,
            size=size or 128,
        )

    def __str__(self):
        return self.get_portrait_url()

    def __getitem__(self, size):
        # Django template will use this after getattr fails
        return self.get_portrait_url(size)


@python_2_unicode_compatible
class Scope(models.Model):
    """
    Represents an access scope granted by SSO.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text=_("The official EVE name fot the scope."))
    help_text = models.TextField(
        help_text=_("The official EVE description of the scope."))

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class AccessToken(models.Model):
    """
    Stores the token returned by SSO callback.
    """
    created = models.DateTimeField(
        auto_now_add=True,
        help_text=_("Datetime when this token was created"))
    updated = models.DateTimeField(
        help_text=_("Datetime when this token was last updated"))
    expires = models.DateTimeField(
        help_text=_("Datetime when access_token expires."))
    invalid = models.BooleanField(
        default=False,
        help_text=_("If true, this token is not valid anymore"))
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        related_name='tokens',
        help_text=_("The user to whom this token belongs."))
    access_token = models.CharField(
        max_length=254,
        unique=True,
        help_text=_("The access token granted by SSO."))
    refresh_token = models.CharField(
        max_length=254,
        blank=True,
        null=True,
        help_text=_("A re-usable token to generate new access tokens upon expiry. "
                    "Only applies when scopes are granted by SSO."))
    scopes = models.ManyToManyField(
        Scope,
        related_name='tokens',
        help_text=_("The access scopes granted by this SSO token."))
    token_type = models.CharField(
        max_length=16,
        choices=(
            ('Character', _("Character")),
            ('Corporation', _("Corporation")),
        ),
        default='Character',
        help_text=_("The applicable range of the token."))
    character_id = models.IntegerField(
        db_index=True,
        help_text=_("The ID of the EVE character who authenticated by SSO."))
    character_name = models.CharField(
        max_length=100,
        help_text=_("The name of the EVE character who authenticated by SSO."))
    character_owner_hash = models.CharField(
        max_length=254,
        help_text=_("The unique string identifying this character and its owning EVE "
                    "account. Changes if the owning account changes."))

    objects = AccessTokenManager()

    def __str__(self):
        return "{} - {}".format(
            self.character_name,
            ", ".join(sorted(s.name for s in self.scopes.all())),
        )

    def __repr__(self):
        return "<{}(id={}): {}, {}>".format(
            self.__class__.__name__,
            self.id,
            self.character_id,
            self.character_name,
        )

    @property
    def can_refresh(self):
        """
        Determines if this token can be refreshed upon expiry
        """
        return bool(self.refresh_token)

    @property
    def expired(self):
        """
        Determines if the access token has expired.
        """
        return self.expires < timezone.now()

    @property
    def valid(self):
        """
        Return true if this token is currently valid
        """
        return not self.invalid and not self.expired

    @property
    def token(self):
        """
        Returns the access token. If expired, automatically refreshes.
        """
        if self.expired:
            if not self.can_refresh:
                raise TokenExpiredError()
            self.refresh()
        return self.access_token

    @property
    def character_portrait(self):
        """
        Return PotraitUrl renderer object
        """
        return PortraitUrl(self.character_id)

    def _update(self, tokens, verify, save_all=False):
        changed = set()
        data = {
            'updated': tokens.updated,
            'expires': tokens.expires,
            'access_token': tokens.access_token,
            'character_id': verify.character_id,
            'character_name': verify.character_name,
            'character_owner_hash': verify.character_owner_hash,
        }

        # update and save changed
        for key, value in data.items():
            if value != getattr(self, key, None):
                setattr(self, key, value)
                changed.add(key)
        self.save(update_fields=None if save_all else list(changed))

        # update scopes
        old_scopes = frozenset((scope.name for scope in self.scopes.all()))
        new_scopes = verify.scopes
        remove_scopes = old_scopes - new_scopes
        add_scopes = new_scopes - old_scopes
        if remove_scopes:
            scopes = Scope.objects.filter(name__in=remove_scopes)
            self.scopes.remove(*remove_scopes)
        if add_scopes:
            scopes = Scope.objects.filter(name__in=add_scopes)
            self.scopes.add(*scopes)

    def refresh(self, crest=None):
        """
        Exchanges refresh token to generate a fresh access token.
        Return True if token is still valid or False if not.
        If token is not refreshable raises NotRefreshableTokenError.
        """
        if not self.can_refresh:
            raise NotRefreshableTokenError()

        # If this token is invalid, do not try to refresh
        if self.invalid:
            return False

        if not crest:
            crest = CrestTokenAPI()

        # Try to refresh
        try:
            tokens = crest.refresh_token(self.refresh_token)
            verify = crest.verify_token(tokens.access_token)
        except TokenInvalidError:
            # Mark token as invalid as crest endpoint reported it to be
            self.invalid = True
            self.save(update_fields=['invalid'])
            return False

        # Token refresh ok, update
        self._update(tokens, verify)
        return True


@python_2_unicode_compatible
class CallbackRedirect(models.Model):
    """
    Records the intended destination for the SSO callback.
    Used to internally redirect SSO callbacks.
    """
    hash_string = models.CharField(
        max_length=128,
        unique=True,
        help_text=_("Cryptographic hash used to reference this callback."))
    salt = models.CharField(
        max_length=32,
        help_text=_("Cryptographic salt used to generate the hash string."))
    created = models.DateTimeField(
        auto_now_add=True)
    session_key = models.CharField(
        max_length=254,
        help_text=_("Session key identifying session this redirect was created for."))
    url = models.CharField(
        max_length=254,
        default='/',
        help_text=_("The internal URL to redirect this callback towards."))
    token = models.ForeignKey(
        AccessToken,
        null=True,
        on_delete=models.CASCADE,
        related_name='callbacks',
        help_text=_("AccessToken generated by a completed code exchange from callback processing."))
    allow_authentication = models.BooleanField(
        default=False,
        help_text=_("If true callback is allowed to authenticate the user"))

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
        req_hash = self.generate_hash(request.session.session_key, self.salt)
        return req_hash == self.hash_string
