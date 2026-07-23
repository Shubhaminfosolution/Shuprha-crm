from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime
from django.conf import settings


class ServicePreset(models.Model):
    name             = models.CharField(max_length=200)
    description      = models.TextField(blank=True)
    default_rate     = models.DecimalField(max_digits=10, decimal_places=2)
    is_active        = models.BooleanField(default=True)
    created_at       = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_service_presets",
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} (₹{self.default_rate})"


# ─────────────────────────────────────────
# AUTO NUMBER GENERATOR
# ─────────────────────────────────────────
def generate_proposal_number():
    year = datetime.date.today().year
    last = Proposal.objects.filter(
        proposal_number__startswith=f'PROP-{year}-'
    ).order_by('-proposal_number').first()
    new_num = (int(last.proposal_number.split('-')[-1]) + 1) if last else 1
    return f"PROP-{year}-{str(new_num).zfill(3)}"


def generate_invoice_number():
    year = datetime.date.today().year
    last = Invoice.objects.filter(
        invoice_number__startswith=f'INV-{year}-'
    ).order_by('-invoice_number').first()
    new_num = (int(last.invoice_number.split('-')[-1]) + 1) if last else 1
    return f"INV-{year}-{str(new_num).zfill(3)}"


# ─────────────────────────────────────────
# PROPOSAL
# ─────────────────────────────────────────
class Proposal(models.Model):

    STATUS_CHOICES = [
        ('draft',    'Draft'),
        ('sent',     'Sent'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    proposal_number      = models.CharField(max_length=30, unique=True, blank=True)
    lead                 = models.ForeignKey(
                               'Leads.Lead',
                               on_delete=models.PROTECT,
                               related_name='proposals'
                           )
    title                = models.CharField(max_length=255)
    status               = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    issue_date           = models.DateField(default=datetime.date.today)
    valid_until          = models.DateField()

    discount             = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gst_percentage       = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # hidden until registration
    notes                = models.TextField(blank=True)

    created_by           = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at           = models.DateTimeField(auto_now_add=True)
    updated_at           = models.DateTimeField(auto_now=True)
    converted_to_invoice = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.proposal_number:
            self.proposal_number = generate_proposal_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.proposal_number} — {self.title}"

    @property
    def subtotal(self):
        return sum(item.amount for item in self.line_items.all())

    @property
    def gst_amount(self):
        return (self.subtotal - self.discount) * self.gst_percentage / 100

    @property
    def total(self):
        return self.subtotal - self.discount + self.gst_amount


# ─────────────────────────────────────────
# INVOICE
# ─────────────────────────────────────────
class Invoice(models.Model):

    PAYMENT_STATUS = [
        ('unpaid',         'Unpaid'),
        ('partially_paid', 'Partially Paid'),
        ('paid',           'Paid'),
    ]

    invoice_number  = models.CharField(max_length=30, unique=True, blank=True)
    lead            = models.ForeignKey(
                          'Leads.Lead',
                          on_delete=models.PROTECT,
                          related_name='invoices'
                      )
    proposal        = models.OneToOneField(
                          Proposal,
                          on_delete=models.SET_NULL,
                          null=True, blank=True,
                          related_name='invoice'
                      )
    title           = models.CharField(max_length=255)
    payment_status  = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='unpaid')

    issue_date      = models.DateField(default=datetime.date.today)
    due_date        = models.DateField()

    discount        = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    gst_percentage  = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # hidden until registration
    amount_paid     = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes           = models.TextField(blank=True)

    created_by      = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = generate_invoice_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.invoice_number} — {self.title}"

    @property
    def subtotal(self):
        return sum(item.amount for item in self.line_items.all())

    @property
    def gst_amount(self):
        return (self.subtotal - self.discount) * self.gst_percentage / 100

    @property
    def total(self):
        return self.subtotal - self.discount + self.gst_amount

    @property
    def balance_due(self):
        return self.total - self.amount_paid


# ─────────────────────────────────────────
# LINE ITEM  (shared by Proposal & Invoice)
# ─────────────────────────────────────────
class LineItem(models.Model):
    proposal       = models.ForeignKey(
                         Proposal, on_delete=models.CASCADE,
                         null=True, blank=True,
                         related_name='line_items'
                     )
    invoice        = models.ForeignKey(
                         Invoice, on_delete=models.CASCADE,
                         null=True, blank=True,
                         related_name='line_items'
                     )
    service_preset = models.ForeignKey(
                         ServicePreset, on_delete=models.SET_NULL,
                         null=True, blank=True
                     )
    description    = models.CharField(max_length=255)
    quantity       = models.DecimalField(max_digits=8, decimal_places=2, default=1)
    unit_price     = models.DecimalField(max_digits=10, decimal_places=2)
    order          = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.description} × {self.quantity}"

    @property
    def amount(self):
        return self.quantity * self.unit_price