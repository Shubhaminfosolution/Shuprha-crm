from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from django.utils import timezone
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from .models import Activity
from .serializers import ActivitySerializer
from rest_framework.decorators import action
from rest_framework.response import Response


class ActivityViewSet(ModelViewSet):
    serializer_class = ActivitySerializer
    premission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role == "admin":
            return Activity.objects.filter(is_deleted=False)
        
        if user.role == "manager":
            return Activity.objects.filter(is_deleted=False)


        return Activity.objects.filter(
            performed_by=user,
            is_deleted = False,
            completed = False,
            scheduled_at_lt= timezone.now()
            )
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["activity_type", "completed", "lead","created_by"]
    ordering_fields = ["scheuled_at", "created_at"]
    @action(detail=False, methods=["get"])
    def my_tasks(self, request):
        leads = Lead.objects.filter(
            assigned_to=request.user,
            activities__completed=False
        ).distinct()

        serializer = self.get_serializer(leads, many=True)
        return Response(serializer.data)
    
    def perform_create(self, serializer):
        serializer.save(performed_by=self.request.user)

    
    