from __future__ import unicode_literals
from django.conf.urls import url
import eve_sso.views

app_name = 'eve_sso'
urlpatterns = [
    url(r'^callback/$', eve_sso.views.receive_callback, name='callback'),
]
