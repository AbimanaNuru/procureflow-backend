from django.utils import timezone
from .models import PurchaseRequest, RequestApprovalLevel, PurchaseOrder, RequestItem
from roles.models import Role


class ApprovalWorkflowService:
    """
    Service class to handle approval workflow logic
    """
    
    @staticmethod
    def create_approval_levels(request, approval_config):
        """
        Create approval levels for a purchase request
        
        Args:
            request: PurchaseRequest instance
            approval_config: List of dicts with 'level' and 'role_id' or 'role_name'
                Example: [
                    {'level': 1, 'role_name': 'manager'},
                    {'level': 2, 'role_name': 'finance'}
                ]
        """
        approval_levels = []
        
        for config in approval_config:
            level = config['level']
            
            # Get role by ID or name
            if 'role_id' in config:
                role = Role.objects.get(id=config['role_id'])
            else:
                role = Role.objects.get(name=config['role_name'])
            
            approval_level = RequestApprovalLevel.objects.create(
                request=request,
                level=level,
                role=role
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
        # Verify approver has the required role
        if approver.role != approval_level.role and not approver.is_superuser:
            raise ValueError(f"User does not have required role: {approval_level.role.name}")
        
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
        # Verify approver has the required role
        if approver.role != approval_level.role and not approver.is_superuser:
            raise ValueError(f"User does not have required role: {approval_level.role.name}")
        
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
        
        Args:
            request: PurchaseRequest instance
        """
        # Check if PO already exists
        if hasattr(request, 'purchase_order') and request.purchase_order:
            return request.purchase_order
        
        # Gather items data
        items_data = []
        if request.items.exists():
            items_data = [
                {
                    'name': item.name,
                    'description': item.description,
                    'quantity': item.quantity,
                    'unit_price': str(item.unit_price),
                    'total_price': str(item.total_price)
                }
                for item in request.items.all()
            ]
        
        # Create purchase order
        po = PurchaseOrder.objects.create(
            vendor='',  # To be filled in later
            items=items_data if items_data else None,
            total_amount=request.amount,
            notes=f"Auto-generated from request: {request.title}"
        )
        
        # Link to request
        request.purchase_order = po
        request.save()
        
        return po
    
    @staticmethod
    def get_pending_approvals_for_user(user):
        """
        Get all pending approvals for a specific user based on their role
        
        Args:
            user: User instance
        
        Returns:
            QuerySet of RequestApprovalLevel instances
        """
        if not user.role:
            return RequestApprovalLevel.objects.none()
        
        # Get approval levels that:
        # 1. Match user's role
        # 2. Are at the current level of the request
        # 3. Are still pending
        return RequestApprovalLevel.objects.filter(
            role=user.role,
            status='pending'
        ).filter(
            request__current_level=models.F('level')
        ).select_related('request', 'role')


# Import models for the F expression
from django.db import models
