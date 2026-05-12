from django.db import models
from encrypted_model_fields.fields import (
    EncryptedCharField,
    EncryptedTextField,
    EncryptedEmailField,
)


class Business(models.Model):
    name = models.CharField(max_length=255)
    website = models.URLField(blank=True)
    contact_person = models.CharField(max_length=255)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=13)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class BusinessProfile(models.Model):
    """
    Sensitive onboarding data for a business.
    All personal/financial fields are AES-256 encrypted at field level.
    Only super admin can write. Client users can only read their own.
    """
    business = models.OneToOneField(
        Business,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    # --- Public fields (unencrypted — safe to filter/display) ---
    industry = models.CharField(max_length=100, blank=True)
    onboarded_at = models.DateTimeField(auto_now_add=True)
    onboarding_notes = models.TextField(blank=True)  # internal visible notes

    # --- Encrypted fields (AES-256 via django-encrypted-model-fields) ---
    # Owner info
    owner_name = EncryptedCharField(max_length=255, blank=True)
    owner_email = EncryptedEmailField(blank=True)
    owner_phone = EncryptedCharField(max_length=20, blank=True)

    # Address
    address = EncryptedTextField(blank=True)

    # Tax / legal
    gst_number = EncryptedCharField(max_length=50, blank=True)
    pan_number = EncryptedCharField(max_length=20, blank=True)

    # Financial
    bank_name = EncryptedCharField(max_length=255, blank=True)
    bank_account_number = EncryptedCharField(max_length=50, blank=True)
    bank_ifsc = EncryptedCharField(max_length=20, blank=True)

    # Contract
    contract_start_date = models.DateField(null=True, blank=True)
    contract_end_date = models.DateField(null=True, blank=True)
    contract_notes = EncryptedTextField(blank=True)
    monthly_budget = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True
    )

    # Internal
    internal_remarks = EncryptedTextField(blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.business.name} — Profile"


class AdAccount(models.Model):
    PLATFORM_CHOICES = [
        ("meta", "Meta"),
        ("google", "Google"),
        ("linkedin", "LinkedIn"),
        ("website", "Website"),
    ]

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="ad_accounts"
    )
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    account_id = models.CharField(max_length=255)
    access_token = EncryptedTextField()  # was plaintext — now encrypted
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.business.name} - {self.platform}"


class AdForm(models.Model):
    account = models.ForeignKey(
        AdAccount,
        on_delete=models.CASCADE,
        related_name="forms"
    )
    form_id = models.CharField(max_length=255, unique=True, db_index=True)
    form_name = models.CharField(max_length=255)
    campaign_name = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.form_name