from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from Leads.models import Lead, Appointment
from .serializers import LeadSerializer, EmailTokenSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import action 
from rest_framework.response import Response
from django.db.models import OuterRef, Subquery
from Activities.models import Activity
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import status
from django.utils.timezone import now
from .serializers import AppointmentSerializer
from Leads.models import Appointment
from django.contrib.auth import logout
from django.shortcuts import redirect




class LeadViewSet(ModelViewSet):
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter]
    search_fields = ['first_name', 'email', 'phone']

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

    queryset = Lead.objects.all()

    @action(detail=True, methods=["POST"])
    def whatsapp_click(self, request, pk=None):
        lead = self.get_object()

        Activity.objects.create(
            lead=lead,
            activity_type="whatsapp",
            notes="Whatsapp chat initiated",
            performed_by=request.user 
        )

        return Response(
            {"message":"Whatsapp activity logged"},
            status = status.HTTP_200_OK
        )




class EmailTokenView(TokenObtainPairView):
    serializer_class = EmailTokenSerializer




@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_data(request):
    user = request.user
    if user.role in ["admin", "manager"]:
        leads = Lead.objects.filter(is_deleted=False)
    else:
        leads = Lead.objects.filter(
            assigned_to= request.user,
            is_deleted= False
        )
    today = timezone.now().date()
    days = int(request.GET.get("days", 7))
    start_date = today - timedelta(days=days)

    # Lead stats
    total_leads = leads.count()
    
    today_leads = leads.filter(created_at__date=today).count()
    # Appointment stats
    total_appointments = Appointment.objects.count()
    completed = Appointment.objects.filter(status="completed").count()


    conversion_rate =(completed/ total_leads * 100) if total_leads else 0
    appointment_rate = (total_appointments/ total_leads * 100) if total_leads else 0 
    # Trend
    leads_trend = (
        leads.filter(created_at__date__gte=start_date)
        .values("created_at__date")
        .annotate(count=Count("id"))
        .order_by("created_at__date")
    )

    # ✅ SOURCE DATA (ADD THIS)
    source_data = list(
        leads.values("source").annotate(count=Count("id"))
    )

    best_source = max(source_data, key=lambda x: x["count"]) ["source"] if source_data else None

    sale_performance = (
        leads.values("assigned_to__email").annotate(count=Count("id"))
    )

    stale_leads = leads.filter(
        status="new",
        created_at__lt=now() - timedelta(days=2)
    ).count()
    


    # ✅ FUNNEL (ADD THIS)
    funnel = {
        "leads": total_leads,
        "appointments": total_appointments,
        "completed": completed,
        "lead_to_appointment":(total_appointments/ total_leads * 100) if total_leads else 0,
        "lead_to_close":(completed/ total_leads * 100) if total_leads else 0,
        "sales_appointment" :list(sale_performance)
    }
    # ✅ TODAY'S APPOINTMENTS
    today_appointments = list(
        Appointment.objects.filter(
            date_time__date=today,
            status="scheduled"
        ).select_related("lead").values(
            "id",
            "lead__first_name",
            "lead__last_name",
            "lead__id",
            "date_time",
            "notes"
        )
    )

    # ✅ TODAY'S ACTIVITIES
    today_activities = list(
        Activity.objects.filter(
            scheduled_at__date=today,
            completed=False,
            is_deleted=False
        ).select_related("lead").values(
            "id",
            "activity_type",
            "lead__first_name",
            "lead__last_name",
            "lead__id",
            "scheduled_at",
            "notes"
        )
    )

    # ✅ TODAY'S FOLLOW-UP LEADS
    today_followups = list(
        Activity.objects.filter(
            scheduled_at__date=today,
            completed=False,
            is_deleted=False,
            activity_type="followup"
        ).select_related("lead").values(
            "id",
            "activity_type",
            "lead__first_name",
            "lead__last_name",
            "lead__id",
            "scheduled_at",
            "notes"
        )
    )

    return JsonResponse({
        "total_leads": total_leads,
        "today_leads": today_leads,
        "total_appointments": total_appointments,
        "completed": completed,
        "leads_trend": list(leads_trend),
        "stale_leads": stale_leads,
        "source_data": list(source_data),
        "best_source": best_source,
        "funnel": funnel,
        "today_appointments": today_appointments,
        "today_activities": today_activities,
        "today_followups": today_followups,
        "conversion_rate": round(conversion_rate, 1),   # ← add this
        "appointment_rate": round(appointment_rate, 1),
    })




def dashboard_page(request):

    return render(request, "dashboard.html")




def leads_page(request):
    return render(request, "leads.html")

def lead_detail_page(request, id):
    return render(request, "lead_detail.html")



def login_page(request):

    return render(request, "login.html")


def appointments_ui(request):
    return render(request, "appointments.html")


def pipeline_ui(request):
    return render(request, "kanban.html")



def logout_view(request):
    logout(request)
    return redirect("/api/v1/login/")



class AppointmentViewSet(ModelViewSet):
    queryset = Appointment.objects.select_related("lead").all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        data = [
            {
                "id": app.id,
                "title": app.lead.first_name,
                "start": app.date_time.isoformat(),
                "status": app.status,          # ✅ Add this for color coding
                "extendedProps": {
                    "notes": app.notes,
                    "status": app.status
                }
            }
            for app in queryset
        ]
        return Response(data)

    # ✅ partial_update is already provided by ModelViewSet — no extra code needed
    # But ensure AppointmentSerializer allows partial updates:
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)