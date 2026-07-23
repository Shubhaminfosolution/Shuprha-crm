from django.db import models
from django.conf import settings


class Client(models.Model):
    STATUS_CHOICES = [
        ("prospect", "Prospect"),
        ("active", "Active"),
        ("inactive", "Inactive"),
    ]

    business = models.ForeignKey(
        "Ads.Business",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clients",
    )

    source_lead = models.OneToOneField(
        "Leads.Lead",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="client",
    )

    company_name = models.CharField(max_length=255, blank=True)
    contact_name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)

    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default="India")
    postal_code = models.CharField(max_length=20, blank=True)

    gstin = models.CharField(max_length=20, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="prospect")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_clients",
    )

    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["business", "status"]),
            models.Index(fields=["email"]),
            models.Index(fields=["phone"]),
        ]

    def __str__(self):
        return self.company_name or self.contact_name