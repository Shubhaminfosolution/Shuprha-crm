from rest_framework import serializers
from django.utils import timezone
from .models import Task


class TaskSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(
        source="created_by.full_name", read_only=True
    )
    assigned_to_name = serializers.CharField(
        source="assigned_to.full_name", read_only=True
    )
    is_overdue = serializers.BooleanField(read_only=True)
    completed_on_time = serializers.BooleanField(read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "due_date",
            "priority",
            "status",
            "assigned_to",
            "assigned_to_name",
            "created_by",
            "created_by_name",
            "completed_at",
            "reminder_sent",
            "is_overdue",
            "completed_on_time",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "created_by",
            "completed_at",
            "reminder_sent",
            "created_at",
            "updated_at",
        ]

    def validate_due_date(self, value):
        if value < timezone.now():
            raise serializers.ValidationError(
                "Due date cannot be in the past."
            )
        return value

    def validate(self, attrs):
        request = self.context.get("request")
        user = request.user if request else None

        # Only creator can edit — enforced at serializer level too
        if self.instance and user:
            if (
                user.role not in ("admin",)
                and self.instance.created_by != user
                # Allow assigned person to only change status to completed
                and not (
                    self.instance.assigned_to == user
                    and set(attrs.keys()) == {"status"}
                    and attrs.get("status") == "completed"
                )
            ):
                raise serializers.ValidationError(
                    "Only the creator or admin can edit this task."
                )
        return attrs