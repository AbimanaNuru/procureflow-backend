from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import update_session_auth_hash
from .models import User
from .serializers import (
    UserSerializer,
    UserDetailSerializer,
    UserRegistrationSerializer,
    ChangePasswordSerializer,
    UserProfileSerializer
)
from .permissions import HasPermission


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing users
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['username', 'email', 'first_name', 'last_name', 'employee_id']
    ordering_fields = ['username', 'created_at', 'date_joined']
    filterset_fields = ['role', 'is_active', 'department']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UserDetailSerializer
        elif self.action == 'create':
            return UserRegistrationSerializer
        elif self.action == 'change_password':
            return ChangePasswordSerializer
        elif self.action == 'profile':
            return UserProfileSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return super().get_permissions()

    @action(detail=False, methods=['get', 'put', 'patch'])
    def profile(self, request):
        """
        Get or update current user's profile
        """
        user = request.user
        
        if request.method == 'GET':
            serializer = UserDetailSerializer(user)
            return Response(serializer.data)
        
        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """
        Change current user's password
        """
        user = request.user
        serializer = ChangePasswordSerializer(data=request.data)

        if serializer.is_valid():
            # Check old password
            if not user.check_password(serializer.data.get('old_password')):
                return Response(
                    {'old_password': ['Wrong password.']},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Set new password
            user.set_password(serializer.data.get('new_password'))
            user.save()
            update_session_auth_hash(request, user)

            return Response(
                {'message': 'Password updated successfully'},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def permissions(self, request, pk=None):
        """
        Get all permissions for a specific user
        """
        user = self.get_object()
        permissions = user.get_permissions()
        return Response({'permissions': permissions})


class RegisterView(generics.CreateAPIView):
    """
    API endpoint for user registration
    """
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer
