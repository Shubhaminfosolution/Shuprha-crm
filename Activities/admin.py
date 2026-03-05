from django.contrib import admin
from .models import Activity

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "lead",
        "activity_type",
        "performed_by",
        "scheduled_at",
        "completed",
        "created_at",
    )

    list_filter = (
        "activity_type",
        "completed",
        "performed_by",
    )

    search_fields = (
        "lead__first_name",
        "lead__email",
    )

    ordering = ("-created_at",)



    def save_model(self, request, obj, form, change):
        if not obj.performed_by:
            obj.performed_by = request.user
        super().save_model(request, obj, form, change)