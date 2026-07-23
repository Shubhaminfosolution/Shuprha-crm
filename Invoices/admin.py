from django.contrib import admin
from .models import ServicePreset, Proposal, Invoice, LineItem


# ── Line item inlines ──────────────────────────────────────
class ProposalLineItemInline(admin.TabularInline):
    model  = LineItem
    fields = ['service_preset', 'description', 'quantity', 'unit_price', 'order']
    extra  = 1
    fk_name = 'proposal'


class InvoiceLineItemInline(admin.TabularInline):
    model  = LineItem
    fields = ['service_preset', 'description', 'quantity', 'unit_price', 'order']
    extra  = 1
    fk_name = 'invoice'


# ── Service Preset ─────────────────────────────────────────
@admin.register(ServicePreset)
class ServicePresetAdmin(admin.ModelAdmin):
    list_display  = ['name', 'default_rate', 'is_active', 'created_at']
    list_filter   = ['is_active']
    search_fields = ['name']


# ── Proposal ───────────────────────────────────────────────
@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display  = ['proposal_number', 'title', 'lead', 'status',
                     'issue_date', 'valid_until', 'converted_to_invoice']
    list_filter   = ['status', 'converted_to_invoice', 'issue_date']
    search_fields = ['proposal_number', 'title', 'lead__first_name']
    readonly_fields = ['proposal_number', 'created_at', 'updated_at']
    inlines       = [ProposalLineItemInline]


# ── Invoice ────────────────────────────────────────────────
@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display  = ['invoice_number', 'title', 'lead', 'payment_status',
                     'issue_date', 'due_date', 'amount_paid']
    list_filter   = ['payment_status', 'issue_date']
    search_fields = ['invoice_number', 'title', 'lead__first_name']
    readonly_fields = ['invoice_number', 'created_at', 'updated_at']
    inlines       = [InvoiceLineItemInline]