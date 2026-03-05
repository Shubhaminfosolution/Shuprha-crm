from rest_framework import serializers
from .models import Lead
from Activities.serializers import ActivitySerializer
from django.utils import timezone


class LeadSerializer(serializers.ModelSerializer):

    activities = ActivitySerializer(many=True, read_only=True)
    next_followup = serializers.SerializerMethodField()

    class Meta:
        model = Lead
        fields = "__all__"

    def get_next_followup(self, obj):
        activity = obj.activities.filter(
            completed=False,
            scheduled_at__gte=timezone.now()
        ).order_by("scheduled_at").first()

        if activity:
            return ActivitySerializer(activity).data
        return None