from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import PurchaseRequest, RequestApprovalLevel, PurchaseOrder, RequestItem
from .serializers import (
    PurchaseRequestSerializer,
    PurchaseRequestDetailSerializer,
    PurchaseRequestCreateSerializer,
    RequestApprovalLevelSerializer,
    PurchaseOrderSerializer,
    RequestItemSerializer,
    ApprovalActionSerializer
)
from .services import ApprovalWorkflowService
from users.permissions import CanCreateRequest, CanApproveRequest, CanViewRequest


class PurchaseRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing purchase requests
    """
    queryset = PurchaseRequest.objects.all()
    serializer_class = PurchaseRequestSerializer
    permission_classes = [IsAuthenticated]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'amount', 'status']
    filterset_fields = ['status', 'created_by']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PurchaseRequestDetailSerializer
        elif self.action == 'create':
            return PurchaseRequestCreateSerializer
        return PurchaseRequestSerializer

    def get_queryset(self):
        """
        Filter requests based on user role
        - Staff can see their own requests
        - Approvers can see requests pending their approval
        - Superusers can see all
        """
        user = self.request.user
        
        if user.is_superuser:
            return PurchaseRequest.objects.all()
        
        # Users can see requests they created
        queryset = PurchaseRequest.objects.filter(
            Q(created_by=user)
        )
        
        # Approvers can also see requests pending their approval
        if user.role:
            queryset = queryset | PurchaseRequest.objects.filter(
                approval_levels__role=user.role,
                approval_levels__status='pending',
                approval_levels__level=models.F('current_level')
            )
        
        return queryset.distinct()

    def perform_create(self, serializer):
        """
        Set the created_by field to current user
        """
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[CanApproveRequest])
    def approve(self, request, pk=None):
        """
        Approve the current approval level
        """
        purchase_request = self.get_object()
        
        # Get current approval level
        approval_level = purchase_request.approval_levels.filter(
            level=purchase_request.current_level
        ).first()
        
        if not approval_level:
            return Response(
                {'error': 'No approval level found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if approval_level.status != 'pending':
            return Response(
                {'error': f'This level is already {approval_level.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate comments
        serializer = ApprovalActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comments = serializer.validated_data.get('comments', '')
        
        try:
            # Approve the level
            ApprovalWorkflowService.approve_level(
                approval_level,
                request.user,
                comments
            )
            
            # Return updated request
            purchase_request.refresh_from_db()
            response_serializer = PurchaseRequestDetailSerializer(purchase_request)
            return Response(response_serializer.data)
        
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )

    @action(detail=True, methods=['post'], permission_classes=[CanApproveRequest])
    def reject(self, request, pk=None):
        """
        Reject the current approval level
        """
        purchase_request = self.get_object()
        
        # Get current approval level
        approval_level = purchase_request.approval_levels.filter(
            level=purchase_request.current_level
        ).first()
        
        if not approval_level:
            return Response(
                {'error': 'No approval level found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if approval_level.status != 'pending':
            return Response(
                {'error': f'This level is already {approval_level.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate comments
        serializer = ApprovalActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comments = serializer.validated_data.get('comments', '')
        
        try:
            # Reject the level
            ApprovalWorkflowService.reject_level(
                approval_level,
                request.user,
                comments
            )
            
            # Return updated request
            purchase_request.refresh_from_db()
            response_serializer = PurchaseRequestDetailSerializer(purchase_request)
            return Response(response_serializer.data)
        
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )

    @action(detail=False, methods=['get'])
    def pending_approvals(self, request):
        """
        Get all requests pending approval by current user
        """
        pending = ApprovalWorkflowService.get_pending_approvals_for_user(request.user)
        requests = PurchaseRequest.objects.filter(
            approval_levels__in=pending
        ).distinct()
        
        serializer = self.get_serializer(requests, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_requests(self, request):
        """
        Get all requests created by current user
        """
        requests = PurchaseRequest.objects.filter(created_by=request.user)
        serializer = self.get_serializer(requests, many=True)
        return Response(serializer.data)


class RequestApprovalLevelViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing approval levels
    """
    queryset = RequestApprovalLevel.objects.all()
    serializer_class = RequestApprovalLevelSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['request', 'level', 'status', 'role']


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing purchase orders
    """
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer
    permission_classes = [IsAuthenticated]
    ordering_fields = ['generated_at', 'total_amount']


class RequestItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing request items
    """
    queryset = RequestItem.objects.all()
    serializer_class = RequestItemSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['request']


# Import models for F expression
from django.db import models
