from django.urls import path
from .views import (
    meta_webhook,
    BusinessListView,
    BusinessProfileView,
    MyBusinessProfileView,
)

urlpatterns = [
    # Meta webhook
    path("meta/webhook/", meta_webhook, name="meta_webhook"),

    # Business list — admin only
    path("businesses/", BusinessListView.as_view(), name="business_list"),

    # BusinessProfile — admin full access, client read-only
    # Admin: GET/POST/PUT /api/v1/businesses/<id>/profile/
    path(
        "businesses/<int:business_id>/profile/",
        BusinessProfileView.as_view(),
        name="business_profile"
    ),

    # Client shortcut — no need to know business_id
    # Client: GET /api/v1/my-profile/
    path(
        "my-profile/",
        MyBusinessProfileView.as_view(),
        name="my_business_profile"
    ),
]