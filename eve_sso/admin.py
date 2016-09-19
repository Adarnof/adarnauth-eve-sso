from __future__ import unicode_literals
from django.contrib import admin
from eve_sso.models import CallbackCode, AccessToken, Scope, CallbackRedirect
from django.contrib.auth import get_user_model

User = get_user_model()

admin.site.register(CallbackCode)
admin.site.register(CallbackRedirect)


@admin.register(Scope)
class ScopeAdmin(admin.ModelAdmin):
    list_display = ('name', 'help_text')


@admin.register(AccessToken)
class AccessTokenAdmin(admin.ModelAdmin):
    @staticmethod
    def get_scopes(obj):
        return ", ".join([x.name for x in obj.scopes.all()])

    get_scopes.short_description = 'Scopes'

    list_display = ('user', 'character_name', 'get_scopes')
    search_fields = ['user__%s' % User.USERNAME_FIELD, 'character_name', 'scopes__name']
