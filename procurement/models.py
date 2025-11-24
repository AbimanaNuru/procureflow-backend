from django.db import models
from django.conf import settings
from roles.models import Role


class PurchaseRequest(models.Model):
    """
    Main purchase request model with multi-level approval tracking
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='requests_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # File uploads
    proforma = models.FileField(upload_to='proformas/', null=True, blank=True)
    receipt = models.FileField(upload_to='receipts/', null=True, blank=True)
    
    # Multi-level approval tracking
    current_level = models.PositiveIntegerField(default=1)
    required_levels = models.PositiveIntegerField(default=2)
    
    # Link to purchase order (created after final approval)
    purchase_order = models.OneToOneField(
        'PurchaseOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='request'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.status}"

    @property
    def is_fully_approved(self):
        """Check if all required approval levels are approved"""
        return self.current_level > self.required_levels

    @property
    def current_approval_level(self):
        """Get the current approval level object"""
        return self.approval_levels.filter(level=self.current_level).first()


class RequestApprovalLevel(models.Model):
    """
    Multi-level approval chain for purchase requests
    Each level represents a stage in the approval process
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    request = models.ForeignKey(
        PurchaseRequest,
        on_delete=models.CASCADE,
        related_name='approval_levels'
    )
    level = models.PositiveIntegerField()  # 1, 2, 3...
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        help_text='Role required to approve this level'
    )
    
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approvals_given'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    comments = models.TextField(blank=True)
    timestamp = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('request', 'level')
        ordering = ['request', 'level']

    def __str__(self):
        return f"{self.request.title} - Level {self.level} ({self.status})"


class PurchaseOrder(models.Model):
    """
    Purchase Order auto-generated after final approval
    """
    # Request is linked via OneToOne in PurchaseRequest model
    
    vendor = models.CharField(max_length=255, null=True, blank=True)
    items = models.JSONField(null=True, blank=True)  # Parsed from proforma or request items
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    generated_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='purchase_orders/', null=True, blank=True)
    
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-generated_at']

    def __str__(self):
        if hasattr(self, 'request'):
            return f"PO - {self.request.title}"
        return f"PO - {self.id}"


class RequestItem(models.Model):
    """
    Line items for purchase requests
    """
    request = models.ForeignKey(
        PurchaseRequest,
        on_delete=models.CASCADE,
        related_name='items'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['request', 'id']

    def save(self, *args, **kwargs):
        # Auto-calculate total price
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} x {self.quantity}"
