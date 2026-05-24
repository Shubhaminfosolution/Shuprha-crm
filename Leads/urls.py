from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import LeadViewSet, dashboard_data, dashboard_page, leads_page, login_page, appointments_ui, AppointmentViewSet, logout_view, lead_detail_page, pipeline_ui, homepage

router = DefaultRouter()
router.register("leads", LeadViewSet, basename="leads")
router.register("appointments", AppointmentViewSet, basename="appointments")

urlpatterns = router.urls + [
    path("dashboard/", dashboard_data, name="dashboard"),
    path("dashboard-ui/", dashboard_page, name="dashboard_page"),
    path("leads-ui/", leads_page, name="leads_ui"),
    path("login/", login_page, name="login"),
    path("appointments-ui/", appointments_ui),
    path("pipeline-ui/", pipeline_ui),
    path("logout/", logout_view),
    path("leads-ui/<int:id>/", lead_detail_page, name="lead_detail"),


]