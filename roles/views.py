from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Role, Permission, RolePermission
from .serializers import (
    RoleSerializer,
    RoleDetailSerializer,
    PermissionSerializer,
    RolePermissionSerializer
)


class RoleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing roles
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return RoleDetailSerializer
        return RoleSerializer

    @action(detail=True, methods=['post'])
    def add_permission(self, request, pk=None):
        """
        Add a permission to a role
        """
        role = self.get_object()
        permission_id = request.data.get('permission_id')

        if not permission_id:
            return Response(
                {'error': 'permission_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            permission = Permission.objects.get(id=permission_id)
        except Permission.DoesNotExist:
            return Response(
                {'error': 'Permission not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        role_permission, created = RolePermission.objects.get_or_create(
            role=role,
            permission=permission
        )

        if created:
            return Response(
                {'message': 'Permission added successfully'},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {'message': 'Permission already exists for this role'},
                status=status.HTTP_200_OK
            )

    @action(detail=True, methods=['post'])
    def remove_permission(self, request, pk=None):
        """
        Remove a permission from a role
        """
        role = self.get_object()
        permission_id = request.data.get('permission_id')

        if not permission_id:
            return Response(
                {'error': 'permission_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            role_permission = RolePermission.objects.get(
                role=role,
                permission_id=permission_id
            )
            role_permission.delete()
            return Response(
                {'message': 'Permission removed successfully'},
                status=status.HTTP_200_OK
            )
        except RolePermission.DoesNotExist:
            return Response(
                {'error': 'Permission not found for this role'},
                status=status.HTTP_404_NOT_FOUND
            )


class PermissionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing permissions
    """
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['code', 'description']
    ordering_fields = ['code', 'created_at']


class RolePermissionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing role-permission relationships
    """
    queryset = RolePermission.objects.all()
    serializer_class = RolePermissionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['role', 'permission']
