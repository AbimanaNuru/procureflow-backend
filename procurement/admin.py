from django.contrib import admin
from .models import PurchaseRequest, RequestApprovalLevel, PurchaseOrder, RequestItem


class RequestItemInline(admin.TabularInline):
    model = RequestItem
    extra = 1


class RequestApprovalLevelInline(admin.TabularInline):
    model = RequestApprovalLevel
    extra = 0
    readonly_fields = ['approver', 'status', 'timestamp']


@admin.register(PurchaseRequest)
class PurchaseRequestAdmin(admin.ModelAdmin):
    list_display = ['title', 'amount', 'status', 'created_by', 'current_level', 'required_levels', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'description', 'created_by__username']
    readonly_fields = ['created_at', 'updated_at', 'purchase_order']
    inlines = [RequestItemInline, RequestApprovalLevelInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'amount', 'status')
        }),
        ('Files', {
            'fields': ('proforma', 'receipt')
        }),
        ('Approval Tracking', {
            'fields': ('current_level', 'required_levels', 'purchase_order')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )


@admin.register(RequestApprovalLevel)
class RequestApprovalLevelAdmin(admin.ModelAdmin):
    list_display = ['request', 'level', 'role', 'status', 'approver', 'timestamp']
    list_filter = ['status', 'role', 'level']
    search_fields = ['request__title', 'approver__username']
    readonly_fields = ['created_at']


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_request_title', 'vendor', 'total_amount', 'generated_at']
    search_fields = ['vendor', 'request__title']
    readonly_fields = ['generated_at']
    
    def get_request_title(self, obj):
        if hasattr(obj, 'request'):
            return obj.request.title
        return '-'
    get_request_title.short_description = 'Request'


@admin.register(RequestItem)
class RequestItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'request', 'quantity', 'unit_price', 'total_price']
    list_filter = ['request']
    search_fields = ['name', 'request__title']
    readonly_fields = ['total_price', 'created_at']
