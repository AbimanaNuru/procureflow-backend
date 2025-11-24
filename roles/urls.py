from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RoleViewSet, PermissionViewSet, RolePermissionViewSet

router = DefaultRouter()
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'permissions', PermissionViewSet, basename='permission')
router.register(r'role-permissions', RolePermissionViewSet, basename='role-permission')

urlpatterns = [
    path('', include(router.urls)),
]
