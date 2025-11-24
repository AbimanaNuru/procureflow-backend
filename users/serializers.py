from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User
from roles.serializers import RoleSerializer


class UserSerializer(serializers.ModelSerializer):
    """
    Basic user serializer for list views
    """
    role_name = serializers.CharField(source='role.name', read_only=True)
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone', 'department', 'employee_id', 'role', 'role_name',
            'permissions', 'is_active', 'date_joined', 'created_at'
        ]
        read_only_fields = ['id', 'date_joined', 'created_at']

    def get_permissions(self, obj):
        return obj.get_permissions()


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Detailed user serializer with role information
    """
    role_detail = RoleSerializer(source='role', read_only=True)
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone', 'department', 'employee_id', 'role', 'role_detail',
            'permissions', 'is_active', 'is_staff', 'date_joined',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'date_joined', 'created_at', 'updated_at']

    def get_permissions(self, obj):
        return obj.get_permissions()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone', 'department',
            'employee_id', 'role'
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password": "Password fields didn't match."
            })
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                "new_password": "Password fields didn't match."
            })
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile updates
    """
    role_name = serializers.CharField(source='role.name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone', 'department', 'employee_id', 'role', 'role_name'
        ]
        read_only_fields = ['id', 'username', 'role']
