from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'department', 'is_active', 'is_staff']
    list_filter = ['role', 'is_active', 'is_staff', 'department']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'employee_id']
    ordering = ['-date_joined']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'phone', 'department', 'employee_id')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'phone', 'department', 'employee_id', 'email', 'first_name', 'last_name')
        }),
    )
