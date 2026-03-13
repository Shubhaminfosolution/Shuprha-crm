from django.contrib import admin
from .models import AdAccount, AdForm, Business

class AdAccountInline(admin.TabularInline):
    model = AdAccount
    extra = 0


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):

    list_display =(
        "id", 
        "name",
        "contact_person",
        "contact_email",
    )

    inlines = [AdAccountInline]


class AdFormInline(admin.TabularInline):
    model = AdForm
    extra = 0

@admin.register(AdAccount)
class AdAccountAdmin(admin.ModelAdmin):

    list_display = [
        "id",
        "business",
        "platform",
        "account_id",
        "is_active",
    ]

    inlines = [AdFormInline]


@admin.register(AdForm)
class AdFormAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "form_name",
        "account",
        "campaign_name",
    )
        
