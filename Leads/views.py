from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from Leads.models import Lead, Appointment
from .serializers import LeadSerializer, EmailTokenSerializer, AppointmentSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.response import Response
from django.db.models import OuterRef, Subquery, Count
from Activities.models import Activity
from Activities.serializers import ActivitySerializer
from django.utils import timezone
from django.utils.timezone import now
from datetime import timedelta
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import status
from django.contrib.auth import logout
from Users.permissions import IsAdmin, IsManager, IsSales, IsInternalOrClient
import csv


class LeadViewSet(ModelViewSet):
    serializer_class = LeadSerializer
    permission_classes = [IsAuthenticated, IsInternalOrClient]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "source", "assigned_to"]
    search_fields = ["first_name", "last_name", "email", "phone"]
    ordering_fields = ["created_at", "score"]

    def get_queryset(self):
        user = self.request.user
        queryset = Lead.objects.filter(is_deleted=False)

        # --- Tenant isolation: ALWAYS scope by business for client users ---
        # This is the security guarantee. Client users can NEVER see
        # leads outside their own business, regardless of query params.
        if user.role == "client":
            queryset = queryset.filter(business=user.business)

        # Internal roles
        elif user.role == "sales":
            queryset = queryset.filter(assigned_to=user)

        elif user.role in ("admin", "manager"):
            # Admin/manager can optionally filter by business
            business_id = self.request.query_params.get("business_id")
            if business_id:
                queryset = queryset.filter(business_id=business_id)

        # Annotate next follow-up activity
        next_activity = Activity.objects.filter(
            lead=OuterRef("pk"),
            completed=False
        ).order_by("scheduled_at")

        return queryset.annotate(
            next_followup_date=Subquery(
                next_activity.values("scheduled_at")[:1]
            )
        ).select_related("business", "assigned_to", "created_by")

    def perform_create(self, serializer):
        user = self.request.user
        # Client users can only create leads under their own business
        if user.role == "client":
            serializer.save(
                created_by=user,
                business=user.business,
                source="manual"
            )
        else:
            serializer.save(created_by=user)

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
        serializer.save(lead=lead, performed_by=request.user)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def whatsapp_click(self, request, pk=None):
        lead = self.get_object()
        Activity.objects.create(
            lead=lead,
            activity_type="whatsapp",
            notes="WhatsApp chat initiated",
            performed_by=request.user
        )
        return Response(
            {"message": "WhatsApp activity logged"},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=["get"])
    def export_csv(self, request):
        """
        Export leads as CSV.
        Client users only get their own business leads.
        Admin/manager can pass ?business_id= to filter.
        """
        queryset = self.get_queryset()

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="leads.csv"'

        writer = csv.writer(response)
        writer.writerow([
            "ID", "First Name", "Last Name", "Email", "Phone",
            "Company", "Status", "Source", "Score",
            "Assigned To", "Business", "Created At"
        ])

        for lead in queryset.values(
            "id", "first_name", "last_name", "email", "phone",
            "company_name", "status", "source", "score",
            "assigned_to__email", "business__name", "created_at"
        ):
            writer.writerow([
                lead["id"],
                lead["first_name"],
                lead["last_name"],
                lead["email"],
                lead["phone"],
                lead["company_name"],
                lead["status"],
                lead["source"],
                lead["score"],
                lead["assigned_to__email"] or "",
                lead["business__name"] or "",
                lead["created_at"].strftime("%Y-%m-%d %H:%M") if lead["created_at"] else "",
            ])

        return response


class EmailTokenView(TokenObtainPairView):
    serializer_class = EmailTokenSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsInternalOrClient])
def dashboard_data(request):
    user = request.user

    # --- Tenant isolation for dashboard ---
    if user.role == "client":
        # Client ONLY sees their own business leads. Hard-coded, not overridable.
        leads = Lead.objects.filter(
            is_deleted=False,
            business=user.business
        )
        appointments = Appointment.objects.filter(
            lead__business=user.business
        )
    elif user.role == "sales":
        leads = Lead.objects.filter(
            assigned_to=user,
            is_deleted=False
        )
        appointments = Appointment.objects.filter(
            lead__assigned_to=user
        )
    else:
        # Admin/manager — can filter by business_id param
        leads = Lead.objects.filter(is_deleted=False)
        appointments = Appointment.objects.all()
        business_id = request.GET.get("business_id")
        if business_id:
            leads = leads.filter(business_id=business_id)
            appointments = appointments.filter(lead__business_id=business_id)

    today = timezone.now().date()
    days = int(request.GET.get("days", 7))
    start_date = today - timedelta(days=days)

    total_leads = leads.count()
    today_leads = leads.filter(created_at__date=today).count()
    total_appointments = appointments.count()
    completed = appointments.filter(status="completed").count()

    conversion_rate = (completed / total_leads * 100) if total_leads else 0
    appointment_rate = (total_appointments / total_leads * 100) if total_leads else 0

    leads_trend = list(
        leads.filter(created_at__date__gte=start_date)
        .values("created_at__date")
        .annotate(count=Count("id"))
        .order_by("created_at__date")
    )

    source_data = list(leads.values("source").annotate(count=Count("id")))
    best_source = max(source_data, key=lambda x: x["count"])["source"] if source_data else None

    stale_leads = leads.filter(
        status="new",
        created_at__lt=now() - timedelta(days=2)
    ).count()

    status_breakdown = list(leads.values("status").annotate(count=Count("id")))

    sale_performance = list(
        leads.values("assigned_to__email").annotate(count=Count("id"))
    )

    funnel = {
        "leads": total_leads,
        "appointments": total_appointments,
        "completed": completed,
        "lead_to_appointment": (total_appointments / total_leads * 100) if total_leads else 0,
        "lead_to_close": (completed / total_leads * 100) if total_leads else 0,
        "sales_appointment": sale_performance,
    }

    today_appointments = list(
        appointments.filter(
            date_time__date=today,
            status="scheduled"
        ).select_related("lead").values(
            "id", "lead__first_name", "lead__last_name",
            "lead__id", "date_time", "notes"
        )
    )

    today_activities = list(
        Activity.objects.filter(
            scheduled_at__date=today,
            completed=False,
            is_deleted=False,
            lead__in=leads
        ).select_related("lead").values(
            "id", "activity_type",
            "lead__first_name", "lead__last_name",
            "lead__id", "scheduled_at", "notes"
        )
    )

    today_followups = list(
        Activity.objects.filter(
            scheduled_at__date=today,
            completed=False,
            is_deleted=False,
            activity_type="followup",
            lead__in=leads
        ).select_related("lead").values(
            "id", "activity_type",
            "lead__first_name", "lead__last_name",
            "lead__id", "scheduled_at", "notes"
        )
    )

    return JsonResponse({
        "total_leads": total_leads,
        "today_leads": today_leads,
        "total_appointments": total_appointments,
        "completed": completed,
        "leads_trend": leads_trend,
        "stale_leads": stale_leads,
        "source_data": source_data,
        "best_source": best_source,
        "status_breakdown": status_breakdown,
        "funnel": funnel,
        "today_appointments": today_appointments,
        "today_activities": today_activities,
        "today_followups": today_followups,
        "conversion_rate": round(conversion_rate, 1),
        "appointment_rate": round(appointment_rate, 1),
    })


# --- UI page views (unchanged) ---

def dashboard_page(request):
    return render(request, "dashboard.html")



def homepage(request):
    return render(request, "Homepage.html")

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
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated, IsInternalOrClient]

    def get_queryset(self):
        user = self.request.user
        if user.role == "client":
            return Appointment.objects.select_related("lead").filter(
                lead__business=user.business
            )
        elif user.role == "sales":
            return Appointment.objects.select_related("lead").filter(
                lead__assigned_to=user
            )
        return Appointment.objects.select_related("lead").all()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        data = [
            {
                "id": app.id,
                "title": app.lead.first_name,
                "start": app.date_time.isoformat(),
                "status": app.status,
                "extendedProps": {
                    "notes": app.notes,
                    "status": app.status,
                }
            }
            for app in queryset
        ]
        return Response(data)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)