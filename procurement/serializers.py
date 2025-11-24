from rest_framework import serializers
from .models import PurchaseRequest, RequestApprovalLevel, PurchaseOrder, RequestItem
from users.serializers import UserSerializer
from roles.serializers import RoleSerializer


class RequestItemSerializer(serializers.ModelSerializer):
    """
    Serializer for request line items
    """
    class Meta:
        model = RequestItem
        fields = ['id', 'name', 'description', 'quantity', 'unit_price', 'total_price', 'created_at']
        read_only_fields = ['id', 'total_price', 'created_at']


class RequestApprovalLevelSerializer(serializers.ModelSerializer):
    """
    Serializer for approval levels
    """
    role_name = serializers.CharField(source='role.name', read_only=True)
    approver_name = serializers.SerializerMethodField()

    class Meta:
        model = RequestApprovalLevel
        fields = [
            'id', 'level', 'role', 'role_name', 'approver', 'approver_name',
            'status', 'comments', 'timestamp', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_approver_name(self, obj):
        if obj.approver:
            return obj.approver.get_full_name() or obj.approver.username
        return None


class PurchaseOrderSerializer(serializers.ModelSerializer):
    """
    Serializer for purchase orders
    """
    request_title = serializers.CharField(source='request.title', read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'request_title', 'vendor', 'items', 'total_amount',
            'generated_at', 'file', 'notes'
        ]
        read_only_fields = ['id', 'generated_at']


class PurchaseRequestSerializer(serializers.ModelSerializer):
    """
    Basic serializer for purchase requests (list view)
    """
    created_by_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseRequest
        fields = [
            'id', 'title', 'description', 'amount', 'status', 'status_display',
            'created_by', 'created_by_name', 'created_at', 'updated_at',
            'current_level', 'required_levels', 'items_count', 'proforma', 'receipt'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at', 'status']

    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() or obj.created_by.username

    def get_items_count(self, obj):
        return obj.items.count()


class PurchaseRequestDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for purchase requests (detail view)
    """
    created_by_detail = UserSerializer(source='created_by', read_only=True)
    approval_levels = RequestApprovalLevelSerializer(many=True, read_only=True)
    items = RequestItemSerializer(many=True, read_only=True)
    purchase_order = PurchaseOrderSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_fully_approved = serializers.BooleanField(read_only=True)

    class Meta:
        model = PurchaseRequest
        fields = [
            'id', 'title', 'description', 'amount', 'status', 'status_display',
            'created_by', 'created_by_detail', 'created_at', 'updated_at',
            'proforma', 'receipt', 'current_level', 'required_levels',
            'is_fully_approved', 'approval_levels', 'items', 'purchase_order'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at', 'status']


class PurchaseRequestCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating purchase requests with items
    """
    items = RequestItemSerializer(many=True, required=False)
    approval_config = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        help_text="List of approval levels: [{'level': 1, 'role_name': 'manager'}, ...]"
    )

    class Meta:
        model = PurchaseRequest
        fields = [
            'title', 'description', 'amount', 'proforma', 'receipt',
            'items', 'approval_config'
        ]

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        approval_config = validated_data.pop('approval_config', None)
        
        # Create the request
        request = PurchaseRequest.objects.create(**validated_data)
        
        # Create items
        for item_data in items_data:
            RequestItem.objects.create(request=request, **item_data)
        
        # Create approval levels if config provided
        if approval_config:
            from .services import ApprovalWorkflowService
            ApprovalWorkflowService.create_approval_levels(request, approval_config)
        
        return request


class ApprovalActionSerializer(serializers.Serializer):
    """
    Serializer for approval/rejection actions
    """
    comments = serializers.CharField(required=False, allow_blank=True)
