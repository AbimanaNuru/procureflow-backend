from rest_framework.permissions import BasePermission


class CanManageProcurement(BasePermission):
    """
    Permission for procurement management
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return request.user.has_permission('manage_procurement')
