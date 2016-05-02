from django.conf.urls import url
import eve_sso.views

urlpatterns = [
    url(r'^redirect/$', eve_sso.views.sso_redirect, name='eve_sso_redirect'),
    url(r'^callback/$', eve_sso.views.receive_callback, name='eve_sso_callback'),
]
