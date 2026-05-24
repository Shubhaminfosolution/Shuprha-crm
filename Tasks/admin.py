from django.contrib import admin
from django.utils import timezone
from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "assigned_to",
        "created_by",
        "priority",
        "status",
        "due_date",
        "completed_at",
        "reminder_sent",
    )

    list_filter = (
        "status",
        "priority",
        "assigned_to",
        "reminder_sent",
    )

    search_fields = (
        "title",
        "description",
        "assigned_to__email",
        "created_by__email",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "completed_at",
        "reminder_sent",
    )

    ordering = ("due_date",)

    fieldsets = (
        ("Task Details", {
            "fields": ("title", "description", "priority", "due_date")
        }),
        ("Assignment", {
            "fields": ("assigned_to", "created_by")
        }),
        ("Status", {
            "fields": ("status", "completed_at", "reminder_sent")
        }),
        ("System", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    actions = ["mark_completed", "mark_overdue"]

    def mark_completed(self, request, queryset):
        queryset.update(status="completed", completed_at=timezone.now())
    mark_completed.short_description = "Mark selected tasks as Completed"

    def mark_overdue(self, request, queryset):
        queryset.update(status="overdue")
    mark_overdue.short_description = "Mark selected tasks as Overdue"