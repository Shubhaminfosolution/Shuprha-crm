import hashlib
import hmac
import json
import logging

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from Users.permissions import IsAdmin, IsInternalOrClient
from .models import Business, BusinessProfile
from .serializers import (
    BusinessProfileAdminSerializer,
    BusinessProfileClientSerializer,
    BusinessSerializer,
)
from .tasks import process_meta_lead_task

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Meta Webhook
# ─────────────────────────────────────────────

@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def meta_webhook(request):

    if request.method == "GET":
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        if mode == "subscribe" and token == settings.META_VERIFY_TOKEN:
            return HttpResponse(challenge, content_type="text/plain")

        return HttpResponse(status=403)

    if request.method == "POST":
        # Verify X-Hub-Signature-256 — rejects fake/forged webhook calls
        sig_header = request.headers.get("X-Hub-Signature-256", "")
        if not _verify_meta_signature(request.body, sig_header):
            logger.warning("Meta webhook signature verification failed")
            return HttpResponse(status=403)

        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return HttpResponse(status=400)

        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                leadgen_id = value.get("leadgen_id")
                form_id = value.get("form_id")

                if leadgen_id and form_id:
                    process_meta_lead_task.delay(leadgen_id, form_id)

        return Response({"status": "ok"})

    return HttpResponse(status=405)


def _verify_meta_signature(body: bytes, sig_header: str) -> bool:
    if not sig_header.startswith("sha256="):
        return False
    app_secret = settings.META_APP_SECRET
    if not app_secret:
        return settings.DEBUG
    expected = "sha256=" + hmac.new(
        app_secret.encode("utf-8"),
        body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, sig_header)


# ─────────────────────────────────────────────
# Business list (admin only)
# ─────────────────────────────────────────────

class BusinessListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        businesses = Business.objects.all().order_by("name")
        serializer = BusinessSerializer(businesses, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = BusinessSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ─────────────────────────────────────────────
# BusinessProfile — create / retrieve / update
# ─────────────────────────────────────────────

class BusinessProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_profile(self, business_id):
        return get_object_or_404(
            BusinessProfile,
            business_id=business_id
        )

    def _check_access(self, request, business_id):
        """
        Admin — full access to any business.
        Client — read-only access to their own business only.
        Anyone else — denied.
        """
        user = request.user
        if user.role == "admin":
            return True
        if user.role == "client":
            return str(user.business_id) == str(business_id)
        return False

    def get(self, request, business_id):
        if not self._check_access(request, business_id):
            return Response(
                {"detail": "You do not have access to this profile."},
                status=status.HTTP_403_FORBIDDEN
            )

        profile = self._get_profile(business_id)

        # Admin gets full data including internal remarks
        # Client gets limited read-only view
        if request.user.role == "admin":
            serializer = BusinessProfileAdminSerializer(profile)
        else:
            serializer = BusinessProfileClientSerializer(profile)

        return Response(serializer.data)

    def post(self, request, business_id):
        # Only admin can create profiles
        if request.user.role != "admin":
            return Response(
                {"detail": "Only admins can create business profiles."},
                status=status.HTTP_403_FORBIDDEN
            )

        business = get_object_or_404(Business, id=business_id)

        # Prevent duplicate profile
        if BusinessProfile.objects.filter(business=business).exists():
            return Response(
                {"detail": "Profile already exists. Use PUT to update."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = BusinessProfileAdminSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(business=business)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request, business_id):
        # Only admin can edit profiles
        if request.user.role != "admin":
            return Response(
                {"detail": "Only admins can edit business profiles."},
                status=status.HTTP_403_FORBIDDEN
            )

        profile = self._get_profile(business_id)
        serializer = BusinessProfileAdminSerializer(
            profile, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


# ─────────────────────────────────────────────
# Client: view own business profile
# ─────────────────────────────────────────────

class MyBusinessProfileView(APIView):
    """
    Endpoint for client users to view their own business profile.
    No business_id needed — derived from request.user.business.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role != "client" or not user.business:
            return Response(
                {"detail": "Only client users with an assigned business can access this."},
                status=status.HTTP_403_FORBIDDEN
            )

        profile = get_object_or_404(BusinessProfile, business=user.business)
        serializer = BusinessProfileClientSerializer(profile)
        return Response(serializer.data)