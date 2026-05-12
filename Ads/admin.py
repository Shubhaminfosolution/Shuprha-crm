from django.contrib import admin
from .models import AdAccount, AdForm, Business, BusinessProfile


class AdAccountInline(admin.TabularInline):
    model = AdAccount
    extra = 0
    # access_token excluded from inline — edit via AdAccount directly
    fields = ("platform", "account_id", "is_active")


class BusinessProfileInline(admin.StackedInline):
    model = BusinessProfile
    extra = 0
    can_delete = False

    # Public fields shown inline
    fields = (
        "industry",
        "onboarded_at",
        "onboarding_notes",
        "contract_start_date",
        "contract_end_date",
        "monthly_budget",
    )
    readonly_fields = ("onboarded_at",)


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "contact_person",
        "contact_email",
        "contact_phone",
        "created_at",
    )
    search_fields = ("name", "contact_email", "contact_person")
    inlines = [AdAccountInline, BusinessProfileInline]


@admin.register(BusinessProfile)
class BusinessProfileAdmin(admin.ModelAdmin):
    """
    Full profile editor — super admin only.
    All encrypted fields are editable here.
    Django admin decrypts transparently on read,
    encrypts on save via django-encrypted-model-fields.
    """
    list_display = (
        "id",
        "get_business_name",
        "industry",
        "onboarded_at",
        "contract_start_date",
        "contract_end_date",
    )

    search_fields = ("business__name",)

    fieldsets = (
        ("Business", {
            "fields": ("business", "industry", "onboarding_notes")
        }),
        ("Owner Info (Encrypted)", {
            "fields": (
                "owner_name",
                "owner_email",
                "owner_phone",
                "address",
            ),
            "classes": ("collapse",),
        }),
        ("Tax & Legal (Encrypted)", {
            "fields": ("gst_number", "pan_number"),
            "classes": ("collapse",),
        }),
        ("Banking (Encrypted)", {
            "fields": (
                "bank_name",
                "bank_account_number",
                "bank_ifsc",
            ),
            "classes": ("collapse",),
        }),
        ("Contract", {
            "fields": (
                "contract_start_date",
                "contract_end_date",
                "monthly_budget",
                "contract_notes",
            ),
            "classes": ("collapse",),
        }),
        ("Internal (Encrypted)", {
            "fields": ("internal_remarks",),
            "classes": ("collapse",),
        }),
    )

    readonly_fields = ("onboarded_at", "updated_at")

    def get_business_name(self, obj):
        return obj.business.name
    get_business_name.short_description = "Business"

    def has_module_perms(self, request, app_label=None):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


class AdFormInline(admin.TabularInline):
    model = AdForm
    extra = 0
    fields = ("form_id", "form_name", "campaign_name")


@admin.register(AdAccount)
class AdAccountAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "business",
        "platform",
        "account_id",
        "is_active",
    )
    list_filter = ("platform", "is_active")
    search_fields = ("business__name", "account_id")
    inlines = [AdFormInline]


@admin.register(AdForm)
class AdFormAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "form_name",
        "form_id",
        "get_business",
        "campaign_name",
        "created_at",
    )
    search_fields = ("form_name", "form_id", "account__business__name")

    def get_business(self, obj):
        return obj.account.business.name
    get_business.short_description = "Business"