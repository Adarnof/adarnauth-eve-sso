from __future__ import unicode_literals
from datetime import timedelta
from celery.task import periodic_task
from django.utils import timezone

from .crest import CrestTokenAPI
from .models import CallbackRedirect, AccessToken


@periodic_task(run_every=timedelta(hours=4))
def cleanup_callbackredirect(max_age=300):
    """
    Delete old :model:`eve_sso.CallbackRedirect` models.
    Accepts a max_age parameter, in seconds (default 300).
    """
    CallbackRedirect.objects.filter(
        created__lte=timezone.now() - timedelta(seconds=max_age),
    ).delete()


@periodic_task(run_every=timedelta(days=1))
def cleanup_accesstoken():
    """
    Delete expired :model:`eve_sso.AccessToken` models.
    """
    crest = CrestTokenAPI()
    for model in AccessToken.objects.get_for_refresh():
        if model.can_refresh:
            model.refresh(crest=crest)
        else:
            model.delete()
