from __future__ import unicode_literals
from celery.task import periodic_task
from django.utils import timezone
from datetime import timedelta
from eve_sso.models import CallbackRedirect, CallbackCode, AccessToken, TokenError

@periodic_task(run_every=timedelta(hours=4))
def cleanup_callbackredirect(max_age=300):
    """
    Delete old :model:`eve_sso.CallbackRedirect` models.
    Accepts a max_age parameter, in seconds (default 300).
    """
    max_age_obj = timedelta(seconds=max_age)
    CallbackRedirect.objects.filter(created__lte=timezone.now()-max_age_obj).delete()

@periodic_task(run_every=timedelta(days=1))
def cleanup_callbackcode(max_age=300):
    """
    Delete old :model:`eve_sso.CallbackCode` models.
    Accepts a max_age parameter, in seconds (default 300).
    """
    max_age_obj = timedelta(seconds=max_age)
    CallbackCode.objects.filter(created__lte=timezone.now()-max_age_obj).delete()

@periodic_task(run_every=timedelta(days=1))
def cleanup_accesstoken():
    """
    Delete expired :model:`eve_sso.AccessToken` models.
    """
    for model in AccessToken.objects.all():
        if model.expired:
            if model.can_refresh:
                try:
                    model.refresh()
                except TokenError:
                    model.delete()
            else:
                model.delete()
