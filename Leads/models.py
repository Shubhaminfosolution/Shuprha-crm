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
    ]

    SOURCE_CHOICES = [
        ("meta ads", "Meta Ads"),
        ("google ads", "Google Ads"),
        ("manual", "Manual"),
        ("website", "Website"),
        ("referral","Referral"),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=12, db_index=True)

    company_name = models.CharField(max_length=255, blank=True)

    source = models.CharField(max_length=45, choices=SOURCE_CHOICES)
    status = models.CharField(max_length=45, choices=STATUS_CHOICES, default="new")

    assigned_to= models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="assigned_leads"
    )


    score = models.IntegerField(default=0)

    is_deleted = models.BooleanField(default=False)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null = True,
        related_name="created_leads"
    )

    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["source"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"



business = models.ForeignKey(
    Business,
    on_delete=models.SET_NULL,
    null=True
)


ad_form = models.ForeignKey(
    AdForm, 
    on_delete=models.SET_NULL,
    null=True
)

source_platform = models.CharField(
    max_length=50, 
    blank=True
)