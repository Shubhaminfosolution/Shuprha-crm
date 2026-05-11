from django.db import models
from django.conf import settings
from Ads.models import Business, AdForm


class Lead(models.Model):

    STATUS_CHOICES = [
        ("new", "New"),
        ("not received", "Not Received"),
        ("busy", "Busy"),
        ("in progress", "In Progress"),
        ("qualified", "Qualified"),
        ("proposal", "Proposal Sent"),
        ("converted", "Converted"),
        ("lost", "Lost"),
        ("spam", "Spam"),
    ]

    SOURCE_CHOICES = [
        ("meta ads", "Meta Ads"),
        ("google ads", "Google Ads"),
        ("whatsapp", "WhatsApp"),
        ("manual", "Manual"),
        ("website", "Website"),
        ("referral", "Referral"),
    ]

    # Core fields
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(db_index=True, blank=True)
    phone = models.CharField(max_length=15, db_index=True)
    company_name = models.CharField(max_length=255, blank=True)

    # Status & source
    source = models.CharField(max_length=45, choices=SOURCE_CHOICES)
    source_platform = models.CharField(max_length=50, blank=True)
    status = models.CharField(
        max_length=45,
        choices=STATUS_CHOICES,
        default="new"
    )

    notes = models.TextField(blank=True, null=True)
    score = models.IntegerField(default=0)

    # Business tenant FK — CRITICAL for isolation
    business = models.ForeignKey(
        Business,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leads',
        db_index=True
    )

    # Meta lead gen tracking
    ad_form = models.ForeignKey(
        AdForm,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leads'
    )

    # Deduplication — prevents same Meta lead being created twice
    # if webhook fires more than once for the same leadgen_id
    meta_lead_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
        db_index=True
    )

    # Assignment
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_leads"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_leads"
    )

    # Soft delete
    is_deleted = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["source"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["business", "status"]),      # composite — fast client dashboard queries
            models.Index(fields=["business", "created_at"]),  # composite — fast trend queries
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Appointment(models.Model):
    lead = models.ForeignKey(
        'Lead',
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    date_time = models.DateTimeField()
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=25,
        choices=[
            ('scheduled', 'Scheduled'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
            ('postponed', 'Postponed'),
        ],
        default='scheduled'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.lead.first_name} - {self.date_time}"