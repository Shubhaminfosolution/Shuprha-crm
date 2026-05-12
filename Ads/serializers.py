from rest_framework import serializers
from .models import Business, BusinessProfile, AdAccount, AdForm


class BusinessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = "__all__"


class BusinessProfileAdminSerializer(serializers.ModelSerializer):
    """
    Full serializer for super admin — all fields readable and writable.
    """
    business_name = serializers.CharField(
        source='business.name', read_only=True
    )

    class Meta:
        model = BusinessProfile
        fields = "__all__"
        read_only_fields = ["onboarded_at", "updated_at"]


class BusinessProfileClientSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for client users.
    Exposes only what the business owner should see about themselves.
    Intentionally excludes internal_remarks and contract_notes.
    """
    business_name = serializers.CharField(
        source='business.name', read_only=True
    )

    class Meta:
        model = BusinessProfile
        fields = [
            "id",
            "business",
            "business_name",
            "industry",
            "onboarded_at",
            "owner_name",
            "owner_email",
            "owner_phone",
            "address",
            "gst_number",
            "pan_number",
            "contract_start_date",
            "contract_end_date",
            "monthly_budget",
        ]
        read_only_fields = fields


class AdAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdAccount
        fields = ["id", "business", "platform", "account_id", "is_active", "created_at"]
        # access_token intentionally excluded — never expose tokens via API


class AdFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdForm
        fields = "__all__"