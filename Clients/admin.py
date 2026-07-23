from django.contrib import admin
from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ["contact_name", "company_name", "email", "phone", "status", "business", "created_at"]
    list_filter = ["status", "business", "created_at"]
    search_fields = ["contact_name", "company_name", "email", "phone"]
    readonly_fields = ["created_at", "updated_at"]