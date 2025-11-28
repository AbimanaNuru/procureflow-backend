from django.utils import timezone
from django.contrib.auth.models import Group
from .models import PurchaseRequest, RequestApprovalLevel, PurchaseOrder, RequestItem


# Import models for the F expression
from django.db import models

def calculate_request_total(request):
    """
    Calculate the total amount of a purchase request based on its items
    """
    total = sum(item.total_price for item in request.items.all())
    request.amount = total
    request.save(update_fields=['amount'])
    return total

def get_approval_config_for_amount(amount):
    """
    Get the approval configuration based on the total amount
    Uses dynamic ApprovalConfig from database
    Falls back to default config if none found
    """
    from .models import ApprovalConfig
    
    # Try to get config from database
    config = ApprovalConfig.get_config_for_amount(amount)
    
    if config:
        # Convert to format expected by create_approval_levels
        return [
            {'level': level.level, 'group_id': level.group.id}
            for level in config.levels.all().order_by('level')
        ]
    
    # Fallback to default configuration if no config found
    # Base config: Manager approval always required
    default_config = [
        {'level': 1, 'group_name': 'Manager'}
    ]
    
    # High value config: Add Finance approval
    if amount > 5000:
        default_config.append({'level': 2, 'group_name': 'Finance'})
        
    return default_config

class ApprovalWorkflowService:
    """
    Service class to handle approval workflow logic
    """
    
    @staticmethod
    def update_approval_workflow(request):
        """
        Update approval workflow based on current request amount
        Only works if request is still pending and hasn't started approval process
        """
        # Only update if request is in initial state (level 1, pending)
        # We check if any approvals have been made
        if request.current_level > 1 or request.approval_levels.filter(status__in=['approved', 'rejected']).exists():
            return
            
        # Clear existing approval levels
        request.approval_levels.all().delete()
        
        # Get new config based on amount
        config = get_approval_config_for_amount(request.amount)
        
        # Create new levels
        ApprovalWorkflowService.create_approval_levels(request, config)

    @staticmethod
    def create_approval_levels(request, approval_config):
        """
        Create approval levels for a purchase request
        
        Args:
            request: PurchaseRequest instance
            approval_config: List of dicts with 'level' and 'group_id' or 'group_name'
                Example: [
                    {'level': 1, 'group_name': 'Manager'},
                    {'level': 2, 'group_name': 'Finance'}
                ]
        """
        approval_levels = []
        
        for config in approval_config:
            level = config['level']
            
            # Get group by ID or name
            if 'group_id' in config:
                group = Group.objects.get(id=config['group_id'])
            else:
                group = Group.objects.get(name=config['group_name'])
            
            approval_level = RequestApprovalLevel.objects.create(
                request=request,
                level=level,
                group=group
            )
            approval_levels.append(approval_level)
        
        # Update required_levels on request
        request.required_levels = len(approval_config)
        request.save()
        
        return approval_levels
    
    @staticmethod
    def approve_level(approval_level, approver, comments=''):
        """
        Approve a specific approval level
        
        Args:
            approval_level: RequestApprovalLevel instance
            approver: User instance
            comments: Optional approval comments
        """
        # Verify approver belongs to the required group
        if not approver.groups.filter(id=approval_level.group.id).exists() and not approver.is_superuser:
            raise ValueError(f"User does not belong to required group: {approval_level.group.name}")
        
        # Mark level as approved
        approval_level.status = 'approved'
        approval_level.approver = approver
        approval_level.comments = comments
        approval_level.timestamp = timezone.now()
        approval_level.save()
        
        # Move to next level
        request = approval_level.request
        request.current_level += 1
        
        # Check if all levels are approved
        if request.current_level > request.required_levels:
            request.status = 'approved'
            # Auto-generate purchase order
            ApprovalWorkflowService.generate_purchase_order(request)
        
        request.save()
        return request
    
    @staticmethod
    def reject_level(approval_level, approver, comments=''):
        """
        Reject a specific approval level
        
        Args:
            approval_level: RequestApprovalLevel instance
            approver: User instance
            comments: Rejection reason
        """
        # Verify approver belongs to the required group
        if not approver.groups.filter(id=approval_level.group.id).exists() and not approver.is_superuser:
            raise ValueError(f"User does not belong to required group: {approval_level.group.name}")
        
        # Mark level as rejected
        approval_level.status = 'rejected'
        approval_level.approver = approver
        approval_level.comments = comments
        approval_level.timestamp = timezone.now()
        approval_level.save()
        
        # Mark entire request as rejected
        request = approval_level.request
        request.status = 'rejected'
        request.save()
        
        return request
    
    @staticmethod
    def generate_purchase_order(request):
        """
        Auto-generate purchase order after final approval
        Generate a purchase order for an approved request
        Uses extracted proforma data if available
        """
        from .models import PurchaseOrder
        
        # Check if PO already exists
        if hasattr(request, 'purchase_order') and request.purchase_order:
            return request.purchase_order
        
        # Get proforma data if available
        proforma_data = request.proforma_data or {}
        
        # Create purchase order with extracted data
        po = PurchaseOrder.objects.create(
            vendor=proforma_data.get('vendor', ''),
            vendor_name=proforma_data.get('vendor', ''),
            vendor_address=proforma_data.get('vendor_address', ''),
            payment_terms=proforma_data.get('payment_terms', ''),
            extracted_items=proforma_data.get('items', []),
            items=[{
                'name': item.name,
                'quantity': item.quantity,
                'unit_price': float(item.unit_price),
                'total': float(item.total_price)
            } for item in request.items.all()],
            total_amount=request.amount
        )
        
        # Link PO to request
        request.purchase_order = po
        request.save()
        
        return po
    
    @staticmethod
    def get_pending_approvals_for_user(user):
        """
        Get all pending approvals for a specific user based on their groups
        
        Args:
            user: User instance
        
        Returns:
            QuerySet of RequestApprovalLevel instances
        """
        user_groups = user.groups.all()
        if not user_groups.exists():
            return RequestApprovalLevel.objects.none()
        
        # Get approval levels that:
        # 1. Match user's groups
        # 2. Are at the current level of the request
        # 3. Are still pending
        return RequestApprovalLevel.objects.filter(
            group__in=user_groups,
            status='pending'
        ).filter(
            request__current_level=models.F('level')
        ).select_related('request', 'group')
