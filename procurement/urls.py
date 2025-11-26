from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PurchaseRequestViewSet,
    RequestApprovalLevelViewSet,
    PurchaseOrderViewSet,
    RequestItemViewSet,
    ApprovalConfigViewSet
)

router = DefaultRouter()
router.register(r'requests', PurchaseRequestViewSet, basename='purchase-request')
router.register(r'approval-levels', RequestApprovalLevelViewSet, basename='approval-level')
router.register(r'purchase-orders', PurchaseOrderViewSet, basename='purchase-order')
router.register(r'items', RequestItemViewSet, basename='request-item')
router.register(r'approval-configs', ApprovalConfigViewSet, basename='approval-config')

urlpatterns = [
    path('', include(router.urls)),
]
