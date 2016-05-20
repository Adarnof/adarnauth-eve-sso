from django.contrib import admin
from eve_sso.models import CallbackCode, AccessToken, Scope, CallbackRedirect

admin.site.register(CallbackCode)
admin.site.register(AccessToken)
admin.site.register(CallbackRedirect)

@admin.register(Scope)
class ScopeAdmin(admin.ModelAdmin):
    list_display = ('name', 'help_text')
