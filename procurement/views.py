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
            {'detail': 'Purchase request updated successfully'},
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
                {'detail': 'Purchase request approved successfully'},
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
                {'detail': 'Purchase request rejected successfully'},
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
                'detail': 'Proforma processed successfully',
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
                'detail': 'Receipt validated',
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
    
    @extend_schema(tags=['AI Document Processing'])
    @action(detail=False, methods=['post'])
    def extract_proforma(self, request):
        """
        Extract data from proforma document and create a purchase request
        Upload a proforma file and get extracted data (vendor, items, prices)
        The data will be saved to the database as a new PurchaseRequest
        
        Required fields:
        - proforma: file upload
        - title: request title (optional, will use vendor name if not provided)
        - description: request description (optional)
        """
        from .document_processing import extract_proforma_data
        from .services import ApprovalWorkflowService
        from decimal import Decimal
        import tempfile
        import os
        
        # Check if file is uploaded
        if 'proforma' not in request.FILES:
            return Response(
                {'error': 'No proforma file uploaded. Please include a file with key "proforma".'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        proforma_file = request.FILES['proforma']
        
        try:
            # Save file temporarily for extraction
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(proforma_file.name)[1]) as tmp_file:
                for chunk in proforma_file.chunks():
                    tmp_file.write(chunk)
                tmp_file_path = tmp_file.name
            
            # Extract data using AI
            extracted_data = extract_proforma_data(tmp_file_path)
            
            # Clean up temp file
            os.unlink(tmp_file_path)
            
            if 'error' in extracted_data:
                return Response(
                    {'error': extracted_data['error'], 'data': extracted_data},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create PurchaseRequest with extracted data
            title = request.data.get('title') or f"Purchase from {extracted_data.get('vendor', 'Unknown Vendor')}"
            description = request.data.get('description') or f"Auto-generated from proforma: {proforma_file.name}"
            
            # Calculate total amount from extracted data
            total_amount = Decimal(str(extracted_data.get('total', 0)))
            
            # Create the purchase request
            purchase_request = PurchaseRequest.objects.create(
                title=title,
                description=description,
                amount=total_amount,
                created_by=request.user,
                proforma=proforma_file,  # Save the actual file
                proforma_data=extracted_data  # Save extracted data
            )
            
            # Create RequestItems from extracted items
            items_created = []
            if 'items' in extracted_data and isinstance(extracted_data['items'], list):
                for item_data in extracted_data['items']:
                    item = RequestItem.objects.create(
                        request=purchase_request,
                        name=item_data.get('name', 'Unknown Item'),
                        description=item_data.get('description', ''),
                        quantity=int(item_data.get('quantity', 1)),
                        unit_price=Decimal(str(item_data.get('unit_price', 0)))
                    )
                    items_created.append({
                        'id': str(item.id),
                        'name': item.name,
                        'quantity': item.quantity,
                        'unit_price': float(item.unit_price),
                        'total_price': float(item.total_price)
                    })
            
            # Recalculate total based on items (in case extraction was inaccurate)
            from .services import calculate_request_total
            calculate_request_total(purchase_request)
            
            # Set up approval workflow
            ApprovalWorkflowService.update_approval_workflow(purchase_request)
            
            # Refresh from database to get updated values
            purchase_request.refresh_from_db()
            
            return Response({
                'success': True,
                'message': 'Proforma processed and purchase request created successfully',
                'request_id': str(purchase_request.id),
                'title': purchase_request.title,
                'amount': float(purchase_request.amount),
                'required_levels': purchase_request.required_levels,
                'items_created': len(items_created),
                'extracted_data': extracted_data,
                'items': items_created
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            # Clean up temp file if it exists
            if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
            
            return Response(
                {'error': f'Error processing proforma: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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
            {'detail': 'Purchase order created successfully'},
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(
            {'detail': 'Purchase order updated successfully'},
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
            {'detail': 'Request item created successfully'},
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(
            {'detail': 'Request item updated successfully'},
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
            {'detail': 'Approval configuration created successfully'},
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(
            {'detail': 'Approval configuration updated successfully'},
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
                    'detail': 'No configuration found for this amount. Default rules will apply.',
                    'amount': amount_str,
                    'config': None
                },
                status=status.HTTP_200_OK
            )
        
        serializer = self.get_serializer(config)
        return Response(serializer.data)


# Import models for F expression
from django.db import models

