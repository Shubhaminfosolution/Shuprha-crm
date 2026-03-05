from rest_framework import serializers 
from .models import Activity

class ActivitySerializer(serializers.ModelSerializer):

    class Meta:
        models = Activity
        fields = "__all__"
        read_only_fields = ("performed_by", "created_at", "updated_at")