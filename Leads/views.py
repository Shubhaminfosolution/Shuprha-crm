from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from .models import Lead
from .serializers import LeadSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import action 
from rest_framework.response import Response


class LeadViewSet(ModelViewSet):
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Lead.objects.filter(is_deleted=False)

        if user.role == "sales":
            queryset = queryset.filter(assigned_to=user)

        next_activity = Activity.objects.filter(
            lead=OuterRef("pk"),
            completed=False
        ).order_by("scheduled_at")

        return queryset.annotate(
            next_followup_date=Subquery(
                next_activity.values("scheduled_at")[:1]
            )
        )
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "source", "assigned_to"]
    search_fields = ["first_name", "last_name", "email", "phone"]
    ordering_fields = ["created_at", "score"]

    @action(detail=True, methods=["get"])
    def timeline(self, request, pk=None):
        lead = self.get_object()
        activities = lead.activities.filter(is_deleted=False)
        serializer = ActivitySerializer(activities, many=True)    
        return Response(serializer.data)
    
    @action(detail=True, methods=["post"])
    def add_activity(self, request, pk=None):
        lead = self.get_object()

        serializer = ActivitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(
            lead=lead,
            performed_by=request.user
        )

        return Response(serializer.data)


    def perform_create(self, serializer):
        serializer.save(created_by = self.request.user)
