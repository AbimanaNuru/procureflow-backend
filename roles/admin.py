from django.contrib import admin
from .models import Role, Permission, RolePermission


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['code', 'description', 'created_at']
    search_fields = ['code', 'description']
    ordering = ['code']


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ['role', 'permission', 'created_at']
    list_filter = ['role', 'permission']
    search_fields = ['role__name', 'permission__code']
