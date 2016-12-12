from __future__ import unicode_literals
import logging
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Q, Count
from django.utils import timezone
from django.utils.six import string_types

from .app_settings import app_settings
from .crest import (
    TokenInvalidError,
    TokenExpiredError,
    CrestTokenAPI,
)


logger = logging.getLogger('eve_sso.managers')


class AccessTokenQueryset(models.QuerySet):
    def require_scopes(self, scopes):
        """
        Filter only tokens that have all of the required scopes
        """
        if isinstance(scopes, string_types):
            scopes = scopes.split()

        if len(scopes) > 2:
            # Create subquery to require all the scopes given
            # this should be faster for larger number of scopes
            ids = (self.filter(scopes__name__in=scopes)
                        .values('id')
                        .annotate(num_scopes=Count('scopes'))
                        .filter(num_scopes=len(scopes))
                        .values_list('id', flat=True))
            return self.filter(id__in=ids)
        else:
            # When there is only few scopes, use multiple joins
            q = self
            for scope in scopes:
                q = q.filter(scopes__name=scope)
            return q

    def require_valid(self):
        return self.filter(invalid=False)


class AccessTokenManager(models.Manager.from_queryset(AccessTokenQueryset)):
    def remove_invalid_tokens(self, tokens, verify):
        """
        Remove tokens that have character whos eve account has changed (owner).
        """
        deleted = self.filter(
            character_id=verify.character_id,
        ).exclude(
            character_owner_hash=verify.character_owner_hash,
        ).delete()
        if deleted:
            logger.info("Deleted %d tokens having wrong owner hash for character %s",
                        deleted, verify.character_id)

    def get_fulfilling_tokens(self, verify):
        """
        Return list of tokens that have same character_id and all the scopes of
        the verify response.
        """
        return self.all().filter(
            character_id=verify.character_id,
        ).require_scopes(
            verify.scopes,
        )

    def get_or_create_from_code(self, code, owner=None, crest=None):
        """
        Resolve code to valid token information, then return ald token with all
        the same scopes and character_id (and is valid) or create new token.
        """
        if not crest:
            crest = CrestTokenAPI()

        # Validate the code. tokens and verify can now be trusted
        tokens = crest.verify_authorization_code(code)
        verify = crest.verify_token(tokens.access_token)

        # For security reasons it's good to remove tokens if character owner has changed
        if app_settings.PURGE_TOKENS_ON_ACCOUNT_CHANGE:
            self.remove_invalid_tokens(tokens, verify)

        # Remove tokens for same character from other owners
        if owner:
            deleted = self.filter(
                Q(character_id=verify.character_id) &
                ~Q(owner=None) &
                ~Q(owner=owner)
            ).delete()
            if deleted:
                logger.info("Deleted %d tokens from old owners of character %s",
                            deleted, verify.character_id)

        # Find if the system already has token that has all the required scopes
        token = None
        for old_token in self.get_fulfilling_tokens(verify):
            if old_token.can_refresh and old_token.refresh(crest=crest):
                # old token is still valid and can be used, so prefer it
                token = old_token
                logger.info("Found valid old token %d for character %d that "
                            "has at least all the same scopes as the new",
                            token.id, verify.character_id)
                break
            elif frozenset(old_token.scopes.all()).issubset(verify.scopes):
                # old token that can't be refreshed (e.g. is invalid) can be
                # removed when new token contains all of scopes of the old
                old_token.delete()
                logger.info("Deleted invalid token for character %d as new "
                            "token supersedes it",
                            verify.character_id)

        # Create and store new token in the database
        if not token:
            token = self.model(
                refresh_token=tokens.refresh_token,
                token_type=verify.token_type,
            )
            token._update(tokens, verify, save_all=True) # saves the token
            logger.info("Created and stored new token %d for character %d",
                        token.id, verify.character_id)

        # Only set owner if there is none
        if owner and not token.owner:
            token.owner = owner
            token.save(update_fields=['owner'])
            logger.info("Set token %d owner to %s", token.id, owner)

        return token

    def get_for_refresh(self):
        return self.filter(
            expires__lt=timezone.now(),
        ).require_valid()


class CallbackRedirectManager(models.Manager):
    """
    Provides additional functionality for creating and retrieving
    :model:`eve_sso.CallbackRedirect` instances.
    """

    def get_or_none(self, *args, **kwargs):
        try:
            return self.get(*args, **kwargs)
        except ObjectDoesNotExist:
            return None

    def create(self, session_key, **kwargs):
        """
        Generates requisite salt and hash string for model creation.
        Validates any provided session key, salt, and hash string match.
        """
        model = self.model
        salt = kwargs.pop('salt', None) or model.generate_salt()
        generated_hash_string = model.generate_hash(session_key, salt)
        hash_string = kwargs.pop('hash_string', generated_hash_string)
        if hash_string != generated_hash_string:
            raise ValueError("Value for `hash_string` is invalid. Leave blank or use .generate_hash(()")

        return super(CallbackRedirectManager, self).create(
            salt=salt,
            hash_string=hash_string,
            session_key=session_key,
            **kwargs)
