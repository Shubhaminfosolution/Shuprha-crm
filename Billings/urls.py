from django.urls import path
from .views import (
    superadmin_dashboard,
    business_list,
    business_detail,
    business_action,
    reset_user_password,
    superadmin_page,
)

urlpatterns = [
    # UI
    path("superadmin/", superadmin_page, name="superadmin_page"),

    # API
    path("superadmin/api/dashboard/", superadmin_dashboard, name="superadmin_dashboard"),
    path("superadmin/api/businesses/", business_list, name="superadmin_business_list"),
    path("superadmin/api/businesses/<int:business_id>/", business_detail, name="superadmin_business_detail"),
    path("superadmin/api/businesses/<int:business_id>/action/", business_action, name="superadmin_business_action"),
    path("superadmin/api/users/<int:user_id>/reset-password/", reset_user_password, name="superadmin_reset_password"),
]