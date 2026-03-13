from django.urls import path
from .views import meta_webhook

urlpatterns = [
    path("meta/webhook/", meta_webhook),
]