import logging
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from .app_settings import app_settings


logger = logging.getLogger('eve_sso.backends')


class CrestTokenAuthenticationBackend(ModelBackend):
    def authenticate(self, crest_token=None):
        """
        Authenticate (find or create) django user
        """
        if not crest_token:
            return None

        # Token has user
        user = crest_token.owner
        if user:
            return user

        # if not find user
        user = self.find_user(crest_token)

        # if not create user
        if not user:
            user = self.create_user(crest_token)
            if user:
                logger.info("%s created new user %s from %s", self.__class__.___name__, user, crest_token)

        # add owner for token
        if user:
            crest_token.owner = user
            crest_token.save(update_fields=['owner'])

        return user

    def find_user(self, token):
        """
        Find user with token. User find function from settings
        """
        # Use provided find function
        func = app_settings.AUTH_USER_FROM_TOKEN_FUNC
        if func:
            return func(token)

        # Use stored tokens to find user
        User = get_user_model()
        users = list(User.objects.filter(tokens__character_id=token.character_id).distinct())
        if len(users) == 1:
            return users[0]

        return None

    def create_user(self, token):
        """
        Create user from crest token if enabled and function is provided in settings
        """
        create_user = app_settings.AUTH_CREATE_UNKNOWN_USER and app_settings.AUTH_USER_FROM_TOKEN_FUNC
        return create_user(token) if create_user else None
