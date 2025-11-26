from rest_framework.permissions import BasePermission


class HasPermission(BasePermission):
    """
    Custom permission class to check if user has specific permission
    Usage in views: permission_classes = [HasPermission]
    Set required_permission attribute in view
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusers have all permissions
        if request.user.is_superuser:
            return True

        # Check if view has required_permission attribute
        required_permission = getattr(view, 'required_permission', None)
        if not required_permission:
            return True

        return request.user.has_perm(required_permission)


class CanCreateRequest(BasePermission):
    """
    Permission to create purchase requests
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return request.user.has_perm('procurement.add_purchaserequest')


class CanApproveRequest(BasePermission):
    """
    Permission to approve purchase requests
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return request.user.has_perm('procurement.approve_purchaserequest')


class CanViewRequest(BasePermission):
    """
    Permission to view purchase requests
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        return request.user.has_perm('procurement.view_purchaserequest')


class IsOwnerOrReadOnly(BasePermission):
    """
    Custom permission to only allow owners of an object to edit it
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True

        # Write permissions are only allowed to the owner
        return obj.created_by == request.user
