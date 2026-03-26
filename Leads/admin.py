from django.contrib import admin
from .models import Lead
from Activities.models import Activity
from import_export.admin import ImportExportModelAdmin
from .resources import LeadResource
from Leads.services.whatsapp_service import generate_whatsapp_link
from django.utils.html import format_html
from django.templatetags.static import static

class ActivityInline(admin.StackedInline):
    model = Activity
    extra = 0
    fields = (
        "activity_type",
        "notes",
        "scheduled_at",
        "completed",
        "performed_by",
    )
    readonly_fields = ("performed_by",)
    show_change_link = True


@admin.register(Lead)
class LeadAdmin(ImportExportModelAdmin):

    resource_class =LeadResource

    list_display = (
        "id",
        "first_name",
        "email",
        "phone",
        "status",
        "whatsapp_button",
        "source",
        "assigned_to",
        "score",
        "created_at",
        
    )

    list_filter = (
        "status",
        "source",
        "assigned_to",
        "created_at",
    )

    search_fields = (
        "first_name",
        "last_name",
        "email",
        "phone",
        "company_name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
    )

    ordering = ("-created_at",)

    list_per_page = 50

 
    inlines = [ActivityInline]

    fieldsets = (
        ("Basic Info", {
            "fields": (
                "first_name",
                "last_name",
                "email",
                "phone",
                "company_name",
            )
        }),
        ("Lead Status", {
            "fields": (
                "status",
                "source",
                "score",
            )
        }),
        ("Assignment", {
            "fields": (
                "assigned_to",
                "created_by",
            )
        }),
        ("System Info", {
            "fields": (
                "created_at",
                "updated_at",
                "is_deleted",
            )
        }),
    )

    def has_import_permission(self, request):
        return request.user.role in ["admin", "manager"]

    def has_export_permission(self, request):
        return request.user.role in ["admin", "manager"]
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        if request.user.role in ["admin", "manager"]:
            return qs

        return qs.filter(is_deleted=False, assigned_to=request.user)

    actions = ["mark_as_contacted", "mark_as_lost"]

    def mark_as_contacted(self, request, queryset):
        queryset.update(status="contacted")

    mark_as_contacted.short_description = "Mark selected leads as Contacted"

    def mark_as_lost(self, request, queryset):
        queryset.update(status="lost")

    mark_as_lost.short_description = "Mark selected leads as Lost"

    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def whatsapp_button(self, obj):
        try:
            link = generate_whatsapp_link(obj.first_name, obj.phone)
            if not link:
                return "-"
            return format_html(
                '<a href="{}" target="_blank">'
                '<svg width="20" height="25" margin-left="10" viewBox="0 0 32 32" fill="#25D366">'
                '<path d="M16 .4C7.3.4.3 7.4.3 16c0 2.8.7 5.5 2.1 7.9L.3 32l8.3-2.2c2.3 1.3 4.9 2 7.7 2 8.7 0 15.7-7 15.7-15.6S24.7.4 16 .4zm0 28.5c-2.4 0-4.7-.6-6.7-1.8l-.5-.3-4.9 1.3 1.3-4.8-.3-.5c-1.3-2-2-4.3-2-6.8 0-7.2 5.9-13 13.1-13 7.2 0 13.1 5.8 13.1 13s-5.9 13-13.1 13zm7.2-9.7c-.4-.2-2.2-1.1-2.6-1.2-.3-.1-.6-.2-.9.2-.3.4-1 1.2-1.2 1.5-.2.2-.4.3-.8.1-.4-.2-1.7-.6-3.2-2-1.2-1-2-2.3-2.2-2.7-.2-.4 0-.6.2-.8.2-.2.4-.4.6-.6.2-.2.3-.4.4-.6.1-.2.1-.5 0-.7-.1-.2-.9-2.1-1.2-2.9-.3-.8-.6-.7-.9-.7h-.8c-.3 0-.7.1-1 .5-.3.4-1.3 1.3-1.3 3.2s1.3 3.7 1.5 4c.2.3 2.6 4 6.3 5.6.9.4 1.6.6 2.1.8.9.3 1.7.3 2.4.2.7-.1 2.2-.9 2.5-1.7.3-.8.3-1.5.2-1.7-.1-.2-.4-.3-.8-.5z"/>'
                '</svg>'
                '</a>',
                link
                )
        except Exception as e:
            return "whatsapp button error"
    whatsapp_button.short_description = "Whatsapp"