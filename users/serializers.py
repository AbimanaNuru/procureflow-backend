from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()


class GroupSerializer(serializers.ModelSerializer):
    """Serializer for Django's Group model"""
    class Meta:
        model = Group
        fields = ['id', 'name']


class UserSerializer(serializers.ModelSerializer):
    """
    Basic user serializer for list views
    """
    groups = GroupSerializer(many=True, read_only=True)
    group_ids = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(),
        many=True,
        write_only=True,
        source='groups',
        required=False
    )

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone', 'department', 'employee_id',
            'groups', 'group_ids',
            'is_active', 'is_staff', 'date_joined'
        ]
        read_only_fields = ['id', 'date_joined']

    def update(self, instance, validated_data):
        groups_data = validated_data.pop('groups', None)
        instance = super().update(instance, validated_data)
        if groups_data is not None:
            instance.groups.set(groups_data)
        return instance


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Detailed user serializer with role information
    """
    groups = GroupSerializer(many=True, read_only=True)
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone', 'department', 'employee_id',
            'groups', 'permissions',
            'is_active', 'is_staff', 'is_superuser', 'date_joined',
            'last_login', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login', 'created_at', 'updated_at']

    def get_permissions(self, obj):
        """Get all permissions for the user"""
        return list(obj.get_all_permissions())


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
    group_ids = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(),
        many=True,
        write_only=True,
        source='groups',
        required=False
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone', 'department',
            'employee_id', 'group_ids'
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password": "Password fields didn't match."
            })
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        groups_data = validated_data.pop('groups', [])
        user = User.objects.create_user(**validated_data)
        if groups_data:
            user.groups.set(groups_data)
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
    groups = GroupSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone', 'department', 'employee_id', 'groups'
        ]
        read_only_fields = ['id', 'username', 'groups']
