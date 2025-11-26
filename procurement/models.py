from django.db import models
from django.conf import settings
from django.contrib.auth.models import Group
import uuid


class PurchaseRequest(models.Model):
    """
    Main purchase request model with multi-level approval tracking
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
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
    
    # Document processing fields
    proforma_data = models.JSONField(
        null=True,
        blank=True,
        help_text='Extracted data from proforma document'
    )
    receipt_data = models.JSONField(
        null=True,
        blank=True,
        help_text='Extracted data from receipt document'
    )
    validation_result = models.JSONField(
        null=True,
        blank=True,
        help_text='Receipt validation results against PO'
    )

    class Meta:
        ordering = ['-created_at']
        permissions = [
            ('approve_purchaserequest', 'Can approve purchase requests'),
            ('reject_purchaserequest', 'Can reject purchase requests'),
        ]

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

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(
        PurchaseRequest,
        on_delete=models.CASCADE,
        related_name='approval_levels'
    )
    level = models.PositiveIntegerField()  # 1, 2, 3...
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        help_text='Group required to approve this level'
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
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.CharField(max_length=255, null=True, blank=True)
    vendor_name = models.CharField(max_length=255, blank=True)
    vendor_address = models.TextField(blank=True)
    payment_terms = models.CharField(max_length=255, blank=True)
    items = models.JSONField(null=True, blank=True)  # Parsed from proforma or request items
    extracted_items = models.JSONField(null=True, blank=True)  # Items extracted from proforma
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
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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


class ApprovalConfig(models.Model):
    """
    Configuration for approval workflows based on amount ranges
    Allows dynamic configuration of approval levels for different purchase amounts
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    min_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        help_text='Minimum amount for this configuration (inclusive)'
    )
    max_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Maximum amount for this configuration (inclusive). Leave blank for unlimited.'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this configuration is currently active'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['min_amount']
        verbose_name = 'Approval Configuration'
        verbose_name_plural = 'Approval Configurations'

    def __str__(self):
        max_display = f"${self.max_amount:,.2f}" if self.max_amount else "Unlimited"
        return f"${self.min_amount:,.2f} - {max_display}"

    def clean(self):
        """Validate that min_amount is less than max_amount"""
        from django.core.exceptions import ValidationError
        if self.max_amount and self.min_amount >= self.max_amount:
            raise ValidationError('Minimum amount must be less than maximum amount')

    @classmethod
    def get_config_for_amount(cls, amount):
        """
        Get the active approval configuration for a given amount
        Returns the first matching active configuration
        """
        from decimal import Decimal
        amount = Decimal(str(amount))
        
        # Find configs where amount falls within range
        configs = cls.objects.filter(
            is_active=True,
            min_amount__lte=amount
        ).filter(
            models.Q(max_amount__gte=amount) | models.Q(max_amount__isnull=True)
        ).order_by('min_amount')
        
        return configs.first()


class ApprovalConfigLevel(models.Model):
    """
    Individual approval level within an approval configuration
    Defines which group must approve at each level
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    config = models.ForeignKey(
        ApprovalConfig,
        on_delete=models.CASCADE,
        related_name='levels'
    )
    level = models.PositiveIntegerField(
        help_text='Approval level number (1, 2, 3, etc.)'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        help_text='Group required to approve this level'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('config', 'level')
        ordering = ['config', 'level']
        verbose_name = 'Approval Configuration Level'
        verbose_name_plural = 'Approval Configuration Levels'

    def __str__(self):
        return f"{self.config} - Level {self.level}: {self.group.name}"

