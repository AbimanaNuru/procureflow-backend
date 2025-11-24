from django.db import models


class Role(models.Model):
    """
    Defines user roles in the system (e.g., staff, manager, finance, admin)
    """
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Permission(models.Model):
    """
    Defines granular permissions (e.g., create_request, approve_request, view_request)
    """
    code = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return self.code


class RolePermission(models.Model):
    """
    Many-to-many relationship between roles and permissions
    """
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='role_permissions')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('role', 'permission')
        ordering = ['role', 'permission']

    def __str__(self):
        return f"{self.role.name} - {self.permission.code}"
