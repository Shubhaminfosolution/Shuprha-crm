from django.db import models


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

    access_token = models.TextField()

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

    form_id = models.CharField(max_length=255)
    form_name = models.CharField(max_length=255)
    campaign_name = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.form_name