from __future__ import unicode_literals
from django.conf.urls import url

from .views import (
    receive_callback,
)

app_name = 'eve_sso'
urlpatterns = [
    url(r'^callback/$', receive_callback, name='callback'),
]
