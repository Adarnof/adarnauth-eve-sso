from django.contrib import admin
from eve_sso.models import CallbackCode, AccessToken, Scope, TokenData, CallbackRedirect

admin.site.register(CallbackCode)
admin.site.register(AccessToken)
admin.site.register(Scope)
admin.site.register(TokenData)
admin.site.register(CallbackRedirect)
