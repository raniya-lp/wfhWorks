from rest_framework.permissions import BasePermission
from rest_framework.permissions import IsAuthenticated

from users import models
from users import configurations


def is_authenticated(self, request, view):
    return IsAuthenticated.has_permission(self, request, view)


class IsSuperUser(BasePermission):
    """
    Allows access only to non admin users.
    """
    def has_permission(self, request, view):
        if not is_authenticated(self, request, view):
            return False

        return bool(request.user and request.user.is_staff)

class IsOrganizationUser(BasePermission):
    """
    Allows access only to non admin users.
    """
    def has_permission(self, request, view):
        if not is_authenticated(self, request, view):
            return False
        return is_user_permitted(request, configurations.ORGANIZATION_USER)


def is_user_permitted(request, role_name):
    if not request.user or request.user.is_staff:
        return False

    organization_role = models.Role.objects.filter(user__id=request.user.id, role=role_name).first()
    if organization_role is None:
        return False
    return True


class IsOrganizationAdmin(BasePermission):
    """
    Allows access only to organization admin users.
    """
    def has_permission(self, request, view):
        if not is_authenticated(self, request, view):
            return False
        return is_user_permitted(request, configurations.ORGANIZATION_ADMIN)


class IsOrganizationManager(BasePermission):
    """
    Allows access only to organization manager users.
    """
    def has_permission(self, request, view):
        if not is_authenticated(self, request, view):
            return False
        return is_user_permitted(request, configurations.ORGANIZATION_MANAGER)


class IsOrganizationScheduler(BasePermission):
    """
    Allows access only to organization executive users.
    """
    def has_permission(self, request, view):
        if not is_authenticated(self, request, view):
            return False
        return is_user_permitted(request,configurations.ORGANIZATION_SCHEDULER)

class IsOrganizationUser(BasePermission):
    """
    Allows access only to organization executive users.
    """
    def has_permission(self, request, view):
        if not is_authenticated(self, request, view):
            return False
        return is_user_permitted(request,configurations.ORGANIZATION_USER)