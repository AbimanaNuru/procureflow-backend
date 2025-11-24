from django.contrib.auth.models import AbstractUser
from django.db import models
from roles.models import Role


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser
    Adds role-based access control
    """
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    phone = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    employee_id = models.CharField(max_length=50, blank=True, unique=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.username} ({self.get_full_name() or self.email})"

    def has_permission(self, permission_code):
        """
        Check if user has a specific permission through their role
        Usage: user.has_permission('approve_request')
        """
        if not self.role:
            return False
        return self.role.role_permissions.filter(
            permission__code=permission_code
        ).exists()

    def get_permissions(self):
        """
        Get all permissions for this user through their role
        """
        if not self.role:
            return []
        return [
            rp.permission.code
            for rp in self.role.role_permissions.select_related('permission').all()
        ]
