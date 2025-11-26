from rest_framework import serializers
from django.contrib.auth.models import Group
from .models import (
    PurchaseRequest, RequestApprovalLevel, PurchaseOrder, RequestItem,
    ApprovalConfig, ApprovalConfigLevel
)
from users.serializers import UserSerializer
from .models import ApprovalConfig, ApprovalConfigLevel


class GroupSimpleSerializer(serializers.ModelSerializer):
    """Simple serializer for Group model"""
    class Meta:
        model = Group
        fields = ['id', 'name']


class RequestItemSerializer(serializers.ModelSerializer):
    """
    Serializer for request line items (standalone endpoint)
    """
    class Meta:
        model = RequestItem
        fields = ['id', 'request', 'name', 'description', 'quantity', 'unit_price', 'total_price', 'created_at']
        read_only_fields = ['id', 'total_price', 'created_at']


class RequestItemNestedSerializer(serializers.ModelSerializer):
    """
    Serializer for request line items when nested in purchase request creation
    The request field is automatically set by the parent serializer
    """
    class Meta:
        model = RequestItem
        fields = ['id', 'name', 'description', 'quantity', 'unit_price', 'total_price', 'created_at']
        read_only_fields = ['id', 'total_price', 'created_at']


class RequestApprovalLevelSerializer(serializers.ModelSerializer):
    """
    Serializer for approval levels
    """
    group_name = serializers.CharField(source='group.name', read_only=True)
    approver_name = serializers.SerializerMethodField()

    class Meta:
        model = RequestApprovalLevel
        fields = [
            'id', 'level', 'group', 'group_name', 'approver', 'approver_name',
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
            'id', 'request_title', 'vendor', 'vendor_name', 'vendor_address',
            'payment_terms', 'items', 'extracted_items', 'total_amount',
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
            'current_level', 'required_levels', 'items_count', 'proforma', 'receipt',
            'proforma_data', 'receipt_data', 'validation_result'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at', 'status',
                           'proforma_data', 'receipt_data', 'validation_result']

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
    items = RequestItemNestedSerializer(many=True, read_only=True)
    purchase_order = PurchaseOrderSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_fully_approved = serializers.BooleanField(read_only=True)

    class Meta:
        model = PurchaseRequest
        fields = [
            'id', 'title', 'description', 'amount', 'status', 'status_display',
            'created_by', 'created_by_detail', 'created_at', 'updated_at',
            'proforma', 'receipt', 'current_level', 'required_levels',
            'is_fully_approved', 'approval_levels', 'items', 'purchase_order',
            'proforma_data', 'receipt_data', 'validation_result'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at', 'status',
                           'proforma_data', 'receipt_data', 'validation_result']


class PurchaseRequestCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating purchase requests with items
    """
    items = RequestItemNestedSerializer(many=True, required=False)
    # approval_config is no longer required as it's dynamic
    # amount is no longer required as it's calculated
    
    class Meta:
        model = PurchaseRequest
        fields = [
            'id', 'title', 'description', 'amount', 'status', 
            'items', 'created_at'
        ]
        read_only_fields = ['id', 'amount', 'status', 'created_at']

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        
        # Create the request (amount defaults to 0)
        request = PurchaseRequest.objects.create(**validated_data)
        
        # Create items
        for item_data in items_data:
            RequestItem.objects.create(request=request, **item_data)
        
        # Calculate total and set up approval workflow
        from .services import calculate_request_total, ApprovalWorkflowService
        
        calculate_request_total(request)
        ApprovalWorkflowService.update_approval_workflow(request)
        
        return request


class ApprovalActionSerializer(serializers.Serializer):
    """
    Serializer for approval/rejection actions
    """
    comments = serializers.CharField(required=False, allow_blank=True)


class ApprovalConfigLevelSerializer(serializers.ModelSerializer):
    """
    Serializer for approval configuration levels
    """
    group_name = serializers.CharField(source='group.name', read_only=True)
    
    class Meta:
        model = ApprovalConfigLevel
        fields = ['id', 'level', 'group', 'group_name', 'created_at']
        read_only_fields = ['id', 'created_at']


class ApprovalConfigLevelNestedSerializer(serializers.ModelSerializer):
    """
    Nested serializer for creating approval config levels
    """
    class Meta:
        model = ApprovalConfigLevel
        fields = ['level', 'group']


class ApprovalConfigSerializer(serializers.ModelSerializer):
    """
    Serializer for approval configurations (list and detail view)
    """
    levels = ApprovalConfigLevelSerializer(many=True, read_only=True)
    levels_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ApprovalConfig
        fields = [
            'id', 'min_amount', 'max_amount', 'is_active',
            'levels', 'levels_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_levels_count(self, obj):
        return obj.levels.count()


class ApprovalConfigCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating approval configurations with nested levels
    """
    levels = ApprovalConfigLevelNestedSerializer(many=True)
    
    class Meta:
        model = ApprovalConfig
        fields = ['id', 'min_amount', 'max_amount', 'is_active', 'levels']
        read_only_fields = ['id']
    
    def validate_levels(self, value):
        """Validate that levels are sequential starting from 1"""
        if not value:
            raise serializers.ValidationError("At least one approval level is required")
        
        levels = [item['level'] for item in value]
        levels.sort()
        
        # Check if levels are sequential starting from 1
        expected_levels = list(range(1, len(levels) + 1))
        if levels != expected_levels:
            raise serializers.ValidationError(
                f"Levels must be sequential starting from 1. Expected {expected_levels}, got {levels}"
            )
        
        return value
    
    def validate(self, data):
        """Validate amount ranges"""
        min_amount = data.get('min_amount')
        max_amount = data.get('max_amount')
        
        if max_amount and min_amount >= max_amount:
            raise serializers.ValidationError({
                'max_amount': 'Maximum amount must be greater than minimum amount'
            })
        
        return data
    
    def create(self, validated_data):
        
        levels_data = validated_data.pop('levels')
        
        # Create the config
        config = ApprovalConfig.objects.create(**validated_data)
        
        # Create levels
        for level_data in levels_data:
            ApprovalConfigLevel.objects.create(config=config, **level_data)
        
        return config

