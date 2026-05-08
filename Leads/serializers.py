from rest_framework import serializers
from .models import Lead, Appointment
from Activities.serializers import ActivitySerializer
from django.utils import timezone
from Leads.services.whatsapp_service import generate_whatsapp_link
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User
from django.contrib.auth import authenticate



class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = "__all__"

        
class LeadSerializer(serializers.ModelSerializer):

    activities = ActivitySerializer(many=True, read_only=True)
    next_followup = serializers.SerializerMethodField()
    appointments = AppointmentSerializer(many=True, read_only=True)

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
    
    def get_whatsapp_link(self, obj):
        return generate_whatsapp_link(obj.first_name,obj.phone)
    



class EmailTokenSerializer(TokenObtainPairSerializer):
    
    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        
        user = authenticate(username=email, password=password)

        if not user:
            raise serializers.ValidationError("Invalid email or password")
        refresh = self.get_token(user)

        return{
            "access":str(refresh.access_token),
        }

    





   