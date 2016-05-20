from django.conf.urls import url
import eve_sso.views

app_name = 'eve_sso'
urlpatterns = [
    url(r'^redirect/$', eve_sso.views.sso_redirect, name='redirect'),
    url(r'^callback/$', eve_sso.views.receive_callback, name='callback'),
]
