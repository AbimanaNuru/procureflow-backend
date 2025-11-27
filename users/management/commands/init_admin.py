from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Initialize groups, permissions, and admin user'

    def handle(self, *args, **options):
        self.stdout.write('Initializing system with Django Groups and Permissions...')

        # 1. Create Groups
        groups_config = {
            'Staff': [
                'procurement.add_purchaserequest',
                'procurement.view_purchaserequest',
                'procurement.change_purchaserequest',
                'procurement.add_requestitem',
                'procurement.view_requestitem',
                'procurement.change_requestitem',
            ],
            'Manager': [
                'procurement.add_purchaserequest',
                'procurement.view_purchaserequest',
                'procurement.change_purchaserequest',
                'procurement.approve_purchaserequest',
                'procurement.reject_purchaserequest',
                'procurement.add_requestitem',
                'procurement.view_requestitem',
                'procurement.change_requestitem',
            ],
            'Finance': [
                'procurement.view_purchaserequest',
                'procurement.approve_purchaserequest',
                'procurement.reject_purchaserequest',
                'procurement.view_purchaseorder',
                'procurement.add_purchaseorder',
                'procurement.change_purchaseorder',
            ],
            'Admin': [
                # Admin gets all permissions
            ],
        }

        for group_name, permission_codenames in groups_config.items():
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(f'Created group: {group_name}')
            
            # Clear existing permissions
            group.permissions.clear()
            
            # Add permissions to group
            for codename in permission_codenames:
                try:
                    app_label, perm_codename = codename.split('.')
                    permission = Permission.objects.get(
                        content_type__app_label=app_label,
                        codename=perm_codename
                    )
                    group.permissions.add(permission)
                except Permission.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'Permission {codename} not found, skipping...')
                    )
            
            self.stdout.write(f'Configured permissions for group: {group_name}')

        # Give Admin group all procurement permissions
        admin_group = Group.objects.get(name='Admin')
        procurement_ct = ContentType.objects.get(app_label='procurement', model='purchaserequest')
        procurement_permissions = Permission.objects.filter(
            content_type__app_label='procurement'
        )
        admin_group.permissions.set(procurement_permissions)
        self.stdout.write('Assigned all procurement permissions to Admin group')

        # 2. Create Superuser
        User = get_user_model()
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'password123')

        if not User.objects.filter(username=username).exists():
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            user.groups.add(admin_group)
            user.save()
            self.stdout.write(f'Created superuser: {username}')
        else:
            user = User.objects.get(username=username)
            if not user.groups.filter(name='Admin').exists():
                user.groups.add(admin_group)
                user.save()
                self.stdout.write(f'Added superuser to Admin group: {username}')
            self.stdout.write(f'Superuser {username} already exists')

        self.stdout.write(self.style.SUCCESS('Initialization complete'))

        # 3. Create Test Users
        self.stdout.write('Creating test users...')
        
        test_users = [
            {
                'username': 'staff_user',
                'email': 'staff@example.com',
                'password': 'password123',
                'group': 'Staff',
                'department': 'Procurement'
            },
            {
                'username': 'manager_user',
                'email': 'manager@example.com',
                'password': 'password123',
                'group': 'Manager',
                'department': 'Management'
            },
            {
                'username': 'finance_user',
                'email': 'finance@example.com',
                'password': 'password123',
                'group': 'Finance',
                'department': 'Finance'
            }
        ]

        for user_data in test_users:
            username = user_data['username']
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=user_data['email'],
                    password=user_data['password'],
                    department=user_data['department']
                )
                
                # Add to group
                group_name = user_data['group']
                try:
                    group = Group.objects.get(name=group_name)
                    user.groups.add(group)
                    self.stdout.write(f'Created user {username} and added to {group_name} group')
                except Group.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'Group {group_name} not found for user {username}'))
            else:
                # Ensure existing user is in the group
                user = User.objects.get(username=username)
                group_name = user_data['group']
                if not user.groups.filter(name=group_name).exists():
                    try:
                        group = Group.objects.get(name=group_name)
                        user.groups.add(group)
                        self.stdout.write(f'Added existing user {username} to {group_name} group')
                    except Group.DoesNotExist:
                        pass
                self.stdout.write(f'User {username} already exists')

        self.stdout.write(self.style.SUCCESS('Test users created successfully'))
        self.stdout.write('----------------------------------------')
        self.stdout.write('Credentials (password: password123):')
        self.stdout.write('  - staff_user (Staff)')
        self.stdout.write('  - manager_user (Manager)')
        self.stdout.write('  - finance_user (Finance)')
        self.stdout.write('----------------------------------------')
