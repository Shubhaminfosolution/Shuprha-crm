from django.contrib import admin
from .models import Subscription, SubscriptionLog


class SubscriptionLogInline(admin.TabularInline):
    model = SubscriptionLog
    extra = 0
    readonly_fields = ("action", "note", "performed_by", "created_at")
    can_delete = False


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "business", "plan", "status",
        "price_per_user", "custom_price",
        "user_count", "mrr",
        "billing_start", "next_billing_date",
    )
    list_filter = ("plan", "status")
    search_fields = ("business__name",)
    readonly_fields = ("created_at", "updated_at")
    inlines = [SubscriptionLogInline]

    def user_count(self, obj):
        return obj.user_count
    user_count.short_description = "Users"

    def mrr(self, obj):
        return f"₹{obj.mrr:,.0f}"
    mrr.short_description = "MRR"


@admin.register(SubscriptionLog)
class SubscriptionLogAdmin(admin.ModelAdmin):
    list_display = ("subscription", "action", "performed_by", "created_at")
    list_filter = ("action",)
    readonly_fields = ("created_at",)