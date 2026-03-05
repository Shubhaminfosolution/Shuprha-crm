from django.contrib import admin
from .models import Lead
from Activities.models import Activity
from import_export.admin import ImportExportModelAdmin
from .resources import LeadResource

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