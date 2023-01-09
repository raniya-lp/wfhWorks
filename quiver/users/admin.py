from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from rest_framework_simplejwt import token_blacklist

from . import models

admin.site.register(models.User, UserAdmin)
admin.site.register(models.Profile)
admin.site.register(models.Organization)
admin.site.register(models.Role)
admin.site.register(models.QuiverApps)
admin.site.register(models.UserAppMappping)
admin.site.register(models.Activity)

# Workaround for issue
#https://github.com/jazzband/djangorestframework-simplejwt/issues/266
class OutstandingTokenAdmin(token_blacklist.admin.OutstandingTokenAdmin):
    def has_delete_permission(self, *args, **kwargs):
        return True
admin.site.unregister(token_blacklist.models.OutstandingToken)
admin.site.register(token_blacklist.models.OutstandingToken, OutstandingTokenAdmin)