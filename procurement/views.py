from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Q
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .models import (
    PurchaseRequest, RequestApprovalLevel, PurchaseOrder, RequestItem,
    ApprovalConfig
)
from .serializers import (
    PurchaseRequestSerializer,
    PurchaseRequestDetailSerializer,
    PurchaseRequestCreateSerializer,
    RequestApprovalLevelSerializer,
    PurchaseOrderSerializer,
    RequestItemSerializer,
    ApprovalActionSerializer,
    ApprovalConfigSerializer,
    ApprovalConfigCreateSerializer
)
from .services import ApprovalWorkflowService
from users.permissions import CanCreateRequest, CanApproveRequest, CanViewRequest


@extend_schema_view(
    list=extend_schema(tags=['Purchase Requests']),
    create=extend_schema(tags=['Purchase Requests']),
    retrieve=extend_schema(tags=['Purchase Requests']),
    update=extend_schema(tags=['Purchase Requests']),
    partial_update=extend_schema(tags=['Purchase Requests']),
    destroy=extend_schema(tags=['Purchase Requests']),
)
class PurchaseRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing purchase requests
    """
    queryset = PurchaseRequest.objects.all()
    serializer_class = PurchaseRequestSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']
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
        Filter requests based on user permissions
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
        user_groups = user.groups.all()
        if user_groups.exists():
            queryset = queryset | PurchaseRequest.objects.filter(
                approval_levels__group__in=user_groups,
                approval_levels__status='pending',
                approval_levels__level=models.F('current_level')
            )
        
        return queryset.distinct()

    def perform_create(self, serializer):
        """
        Set the created_by field to current user
        """
        serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(
            {'message': 'Purchase request updated successfully'},
            status=status.HTTP_200_OK
        )

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    @extend_schema(tags=['Approvals'])
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
            
            return Response(
                {'message': 'Purchase request approved successfully'},
                status=status.HTTP_200_OK
            )
        
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )

    @extend_schema(tags=['Approvals'])
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
            
            return Response(
                {'message': 'Purchase request rejected successfully'},
                status=status.HTTP_200_OK
            )
        
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )

    @extend_schema(tags=['Approvals'])
    @action(detail=False, methods=['get'])
    def pending_approvals(self, request):
        """
        Get requests pending approval by current user
        """
        user = request.user
        user_groups = user.groups.all()
        
        if not user_groups.exists():
            return Response([], status=status.HTTP_200_OK)
        
        pending_requests = PurchaseRequest.objects.filter(
            approval_levels__group__in=user_groups,
            approval_levels__status='pending',
            approval_levels__level=models.F('current_level')
        ).distinct()
        
        serializer = self.get_serializer(pending_requests, many=True)
        return Response(serializer.data)
    
    @extend_schema(tags=['AI Document Processing'])
    @action(detail=True, methods=['post'])
    def process_proforma(self, request, pk=None):
        """
        Extract data from uploaded proforma document
        """
        from .document_processing import extract_proforma_data
        import os
        
        purchase_request = self.get_object()
        
        # Check if file is being uploaded in this request
        if 'proforma' in request.FILES:
            purchase_request.proforma = request.FILES['proforma']
            purchase_request.save()
        
        if not purchase_request.proforma:
            return Response(
                {'error': 'No proforma file uploaded. Please upload it first or include it in this request.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get file path
            file_path = purchase_request.proforma.path
            
            # Extract data
            extracted_data = extract_proforma_data(file_path)
            
            # Store extracted data
            purchase_request.proforma_data = extracted_data
            purchase_request.save()
            
            return Response({
                'message': 'Proforma processed successfully',
                'data': extracted_data
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': f'Error processing proforma: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(tags=['AI Document Processing'])
    @action(detail=True, methods=['post'])
    def validate_receipt(self, request, pk=None):
        """
        Validate uploaded receipt against purchase order
        """
        from .document_processing import validate_receipt as validate_receipt_func
        
        purchase_request = self.get_object()
        
        # Check if file is being uploaded in this request
        if 'receipt' in request.FILES:
            purchase_request.receipt = request.FILES['receipt']
            purchase_request.save()
        
        if not purchase_request.receipt:
            return Response(
                {'error': 'No receipt file uploaded. Please upload it first or include it in this request.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not purchase_request.purchase_order:
            return Response(
                {'error': 'No purchase order exists for this request'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get file path
            receipt_path = purchase_request.receipt.path
            
            # Validate receipt
            validation_result = validate_receipt_func(
                receipt_path,
                purchase_request.purchase_order
            )
            
            # Store validation results
            purchase_request.validation_result = validation_result
            if 'receipt_data' in validation_result:
                purchase_request.receipt_data = validation_result['receipt_data']
            purchase_request.save()
            
            return Response({
                'message': 'Receipt validated',
                'validation': validation_result
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': f'Error validating receipt: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(tags=['Purchase Requests'])
    @action(detail=False, methods=['get'])
    def my_requests(self, request):
        """
        Get all requests created by current user
        """
        requests = PurchaseRequest.objects.filter(created_by=request.user)
        
        page = self.paginate_queryset(requests)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(requests, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(tags=['Approvals']),
    retrieve=extend_schema(tags=['Approvals']),
)
class RequestApprovalLevelViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing approval levels
    """
    queryset = RequestApprovalLevel.objects.all()
    serializer_class = RequestApprovalLevelSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'head', 'options']
    filterset_fields = ['request', 'level', 'status', 'role']


@extend_schema_view(
    list=extend_schema(tags=['Purchase Orders']),
    create=extend_schema(tags=['Purchase Orders']),
    retrieve=extend_schema(tags=['Purchase Orders']),
    update=extend_schema(tags=['Purchase Orders']),
    partial_update=extend_schema(tags=['Purchase Orders']),
    destroy=extend_schema(tags=['Purchase Orders']),
)
class PurchaseOrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing purchase orders
    """
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']
    ordering_fields = ['generated_at', 'total_amount']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {'message': 'Purchase order created successfully'},
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(
            {'message': 'Purchase order updated successfully'},
            status=status.HTTP_200_OK
        )

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


@extend_schema_view(
    list=extend_schema(tags=['Request Items']),
    create=extend_schema(tags=['Request Items']),
    retrieve=extend_schema(tags=['Request Items']),
    update=extend_schema(tags=['Request Items']),
    partial_update=extend_schema(tags=['Request Items']),
    destroy=extend_schema(tags=['Request Items']),
)
class RequestItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing request items
    """
    queryset = RequestItem.objects.all()
    serializer_class = RequestItemSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']
    filterset_fields = ['request']

    def check_request_editable(self, purchase_request):
        """
        Check if the request can be edited (must be pending and at level 1)
        """
        if purchase_request.status != 'pending' or purchase_request.current_level > 1:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(
                "Cannot modify items after approval process has started. "
                "Current status: {}, Level: {}".format(
                    purchase_request.status, purchase_request.current_level
                )
            )

    def perform_create(self, serializer):
        purchase_request = serializer.validated_data['request']
        self.check_request_editable(purchase_request)
        serializer.save()
        
        # Update total and workflow
        from .services import calculate_request_total, ApprovalWorkflowService
        calculate_request_total(purchase_request)
        ApprovalWorkflowService.update_approval_workflow(purchase_request)

    def perform_update(self, serializer):
        purchase_request = serializer.instance.request
        self.check_request_editable(purchase_request)
        serializer.save()
        
        # Update total and workflow
        from .services import calculate_request_total, ApprovalWorkflowService
        calculate_request_total(purchase_request)
        ApprovalWorkflowService.update_approval_workflow(purchase_request)

    def perform_destroy(self, instance):
        purchase_request = instance.request
        self.check_request_editable(purchase_request)
        instance.delete()
        
        # Update total and workflow
        from .services import calculate_request_total, ApprovalWorkflowService
        calculate_request_total(purchase_request)
        ApprovalWorkflowService.update_approval_workflow(purchase_request)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {'message': 'Request item created successfully'},
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(
            {'message': 'Request item updated successfully'},
            status=status.HTTP_200_OK
        )

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


@extend_schema_view(
    list=extend_schema(tags=['Approval Configuration']),
    create=extend_schema(tags=['Approval Configuration']),
    retrieve=extend_schema(tags=['Approval Configuration']),
    update=extend_schema(tags=['Approval Configuration']),
    partial_update=extend_schema(tags=['Approval Configuration']),
    destroy=extend_schema(tags=['Approval Configuration']),
)
class ApprovalConfigViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing approval configurations
    Admins can create/update/delete configurations
    All authenticated users can view configurations
    """
    queryset = ApprovalConfig.objects.all()
    serializer_class = ApprovalConfigSerializer
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']
    ordering_fields = ['min_amount', 'created_at']
    filterset_fields = ['is_active']
    
    def get_permissions(self):
        """
        Read operations: IsAuthenticated
        Write operations: IsAdminUser
        """
        if self.action in ['list', 'retrieve', 'get_for_amount']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ApprovalConfigCreateSerializer
        return ApprovalConfigSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {'message': 'Approval configuration created successfully'},
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(
            {'message': 'Approval configuration updated successfully'},
            status=status.HTTP_200_OK
        )
    
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    @extend_schema(tags=['Approval Configuration'])
    @action(detail=False, methods=['get'])
    def get_for_amount(self, request):
        """
        Get the approval configuration for a specific amount
        Query param: amount (required)
        """
        amount_str = request.query_params.get('amount')
        
        if not amount_str:
            return Response(
                {'error': 'amount query parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from decimal import Decimal
            amount = Decimal(amount_str)
        except:
            return Response(
                {'error': 'Invalid amount value'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        config = ApprovalConfig.get_config_for_amount(amount)
        
        if not config:
            return Response(
                {
                    'message': 'No configuration found for this amount. Default rules will apply.',
                    'amount': amount_str,
                    'config': None
                },
                status=status.HTTP_200_OK
            )
        
        serializer = self.get_serializer(config)
        return Response(serializer.data)


# Import models for F expression
from django.db import models

