from rest_framework import serializers
from .models import Role, Permission, RolePermission


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'code', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class RolePermissionSerializer(serializers.ModelSerializer):
    permission = PermissionSerializer(read_only=True)
    permission_id = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.all(),
        source='permission',
        write_only=True
    )

    class Meta:
        model = RolePermission
        fields = ['id', 'role', 'permission', 'permission_id', 'created_at']
        read_only_fields = ['id', 'created_at']


class RoleSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()
    permission_count = serializers.SerializerMethodField()

    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'permissions', 'permission_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_permissions(self, obj):
        role_permissions = obj.role_permissions.all()
        return PermissionSerializer([rp.permission for rp in role_permissions], many=True).data

    def get_permission_count(self, obj):
        return obj.role_permissions.count()


class RoleDetailSerializer(serializers.ModelSerializer):
    role_permissions = RolePermissionSerializer(many=True, read_only=True)

    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'role_permissions', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
