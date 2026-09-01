from django.db import models
from django.utils import timezone


class Subscription(models.Model):

    PLAN_CHOICES = [
        ("starter", "Starter"),
        ("growth", "Growth"),
        ("pro", "Pro"),
        ("custom", "Custom"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("suspended", "Suspended"),
        ("cancelled", "Cancelled"),
    ]

    business = models.OneToOneField(
        'Ads.Business',
        on_delete=models.CASCADE,
        related_name='subscription'
    )

    plan = models.CharField(
        max_length=20,
        choices=PLAN_CHOICES,
        default="starter"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active"
    )

    price_per_user = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=499.00
    )

    razorpay_subscription_id = models.CharField(
        max_length=255, blank=True, null=True
    )
    razorpay_customer_id = models.CharField(
        max_length=255, blank=True, null=True
    )

    billing_start = models.DateField(default=timezone.now)
    next_billing_date = models.DateField(null=True, blank=True)

    custom_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True
    )

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.business.name} — {self.plan} ({self.status})"

    @property
    def user_count(self):
        return self.business.users.filter(
            is_active=True, is_deleted=False
        ).exclude(role="client").count()

    @property
    def mrr(self):
        if self.status != "active":
            return 0
        price = self.custom_price or self.price_per_user
        return float(price) * self.user_count


class SubscriptionLog(models.Model):
    ACTION_CHOICES = [
        ("created", "Created"),
        ("activated", "Activated"),
        ("suspended", "Suspended"),
        ("cancelled", "Cancelled"),
        ("plan_changed", "Plan Changed"),
        ("price_changed", "Price Changed"),
        ("payment_received", "Payment Received"),
        ("payment_failed", "Payment Failed"),
    ]

    subscription = models.ForeignKey(
        Subscription, on_delete=models.CASCADE, related_name='logs'
    )
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    note = models.TextField(blank=True)
    performed_by = models.ForeignKey(
        'Users.User', on_delete=models.SET_NULL,
        null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subscription.business.name} — {self.action}"