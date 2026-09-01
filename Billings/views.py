import logging
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from Users.permissions import IsAdmin
from Ads.models import Business
from Leads.models import Lead
from .models import Subscription, SubscriptionLog

User = get_user_model()
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Super Admin Dashboard — KPIs
# ─────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdmin])
def superadmin_dashboard(request):
    """
    Top-level KPIs for the super admin panel.
    """
    now = timezone.now()
    this_month_start = now.replace(day=1, hour=0, minute=0, second=0)

    total_businesses = Business.objects.count()
    total_users = User.objects.filter(
        is_active=True, is_deleted=False
    ).exclude(role="client").count()
    total_leads = Lead.objects.filter(is_deleted=False).count()
    new_businesses_this_month = Business.objects.filter(
        created_at__gte=this_month_start
    ).count()
    new_leads_this_month = Lead.objects.filter(
        created_at__gte=this_month_start,
        is_deleted=False
    ).count()

    # MRR calculation
    subscriptions = Subscription.objects.filter(status="active").select_related("business")
    total_mrr = sum(s.mrr for s in subscriptions)

    active_businesses = Subscription.objects.filter(status="active").count()
    inactive_businesses = total_businesses - active_businesses

    # Revenue per business
    revenue_breakdown = [
        {
            "business_id": s.business.id,
            "business_name": s.business.name,
            "plan": s.plan,
            "status": s.status,
            "user_count": s.user_count,
            "mrr": s.mrr,
        }
        for s in subscriptions
    ]
    revenue_breakdown.sort(key=lambda x: x["mrr"], reverse=True)

    return Response({
        "total_businesses": total_businesses,
        "total_users": total_users,
        "total_leads": total_leads,
        "total_mrr": round(total_mrr, 2),
        "active_businesses": active_businesses,
        "inactive_businesses": inactive_businesses,
        "new_businesses_this_month": new_businesses_this_month,
        "new_leads_this_month": new_leads_this_month,
        "revenue_breakdown": revenue_breakdown,
    })


# ─────────────────────────────────────────────
# Business List — table + expandable detail
# ─────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdmin])
def business_list(request):
    """All businesses with stats for the admin table."""
    businesses = Business.objects.all().order_by("-created_at")
    data = []

    for biz in businesses:
        users = biz.users.filter(is_active=True, is_deleted=False).exclude(role="client")
        leads = Lead.objects.filter(business=biz, is_deleted=False)
        sub = getattr(biz, 'subscription', None)

        data.append({
            "id": biz.id,
            "name": biz.name,
            "contact_person": biz.contact_person,
            "contact_email": biz.contact_email,
            "contact_phone": biz.contact_phone,
            "website": biz.website,
            "created_at": biz.created_at,
            "user_count": users.count(),
            "lead_count": leads.count(),
            "leads_this_month": leads.filter(
                created_at__gte=timezone.now().replace(day=1)
            ).count(),
            "subscription": {
                "plan": sub.plan if sub else None,
                "status": sub.status if sub else "no_subscription",
                "mrr": sub.mrr if sub else 0,
                "price_per_user": float(sub.price_per_user) if sub else 499,
                "custom_price": float(sub.custom_price) if sub and sub.custom_price else None,
                "billing_start": sub.billing_start if sub else None,
                "next_billing_date": sub.next_billing_date if sub else None,
            } if sub else None,
        })

    return Response(data)


# ─────────────────────────────────────────────
# Business Detail — expandable view
# ─────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdmin])
def business_detail(request, business_id):
    """Full detail for one business — users, leads, subscription logs."""
    biz = get_object_or_404(Business, id=business_id)
    users = biz.users.filter(is_deleted=False).values(
        "id", "email", "full_name", "role", "is_active", "created_at"
    )
    leads = Lead.objects.filter(business=biz, is_deleted=False)
    sub = getattr(biz, 'subscription', None)
    logs = SubscriptionLog.objects.filter(
        subscription=sub
    ).order_by("-created_at").values(
        "action", "note", "performed_by__email", "created_at"
    ) if sub else []

    return Response({
        "id": biz.id,
        "name": biz.name,
        "contact_person": biz.contact_person,
        "contact_email": biz.contact_email,
        "contact_phone": biz.contact_phone,
        "website": biz.website,
        "created_at": biz.created_at,
        "users": list(users),
        "lead_stats": {
            "total": leads.count(),
            "new": leads.filter(status="new").count(),
            "converted": leads.filter(status="converted").count(),
            "lost": leads.filter(status="lost").count(),
        },
        "subscription": {
            "plan": sub.plan if sub else None,
            "status": sub.status if sub else "no_subscription",
            "mrr": sub.mrr if sub else 0,
            "price_per_user": float(sub.price_per_user) if sub else 499,
            "custom_price": float(sub.custom_price) if sub and sub.custom_price else None,
            "billing_start": str(sub.billing_start) if sub else None,
            "next_billing_date": str(sub.next_billing_date) if sub and sub.next_billing_date else None,
            "logs": list(logs),
        } if sub else None,
    })


# ─────────────────────────────────────────────
# Business Actions
# ─────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdmin])
def business_action(request, business_id):
    """
    Perform admin actions on a business.
    Actions: suspend, activate, cancel, change_plan, change_price
    """
    biz = get_object_or_404(Business, id=business_id)
    action = request.data.get("action")
    note = request.data.get("note", "")

    sub, created = Subscription.objects.get_or_create(
        business=biz,
        defaults={"status": "active", "plan": "starter"}
    )

    if action == "suspend":
        sub.status = "suspended"
        sub.save()
        _log(sub, "suspended", note, request.user)
        return Response({"message": f"{biz.name} suspended."})

    elif action == "activate":
        sub.status = "active"
        sub.save()
        _log(sub, "activated", note, request.user)
        return Response({"message": f"{biz.name} activated."})

    elif action == "cancel":
        sub.status = "cancelled"
        sub.save()
        _log(sub, "cancelled", note, request.user)
        return Response({"message": f"{biz.name} cancelled."})

    elif action == "change_plan":
        new_plan = request.data.get("plan")
        if new_plan not in dict(Subscription.PLAN_CHOICES):
            return Response(
                {"error": "Invalid plan."},
                status=status.HTTP_400_BAD_REQUEST
            )
        old_plan = sub.plan
        sub.plan = new_plan
        sub.save()
        _log(sub, "plan_changed", f"{old_plan} → {new_plan}. {note}", request.user)
        return Response({"message": f"Plan changed to {new_plan}."})

    elif action == "change_price":
        new_price = request.data.get("custom_price")
        if not new_price:
            return Response(
                {"error": "custom_price required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        sub.custom_price = new_price
        sub.save()
        _log(sub, "price_changed", f"Custom price set to ₹{new_price}. {note}", request.user)
        return Response({"message": f"Custom price set to ₹{new_price}."})

    elif action == "delete":
        if not request.user.is_superuser:
            return Response(
                {"error": "Only superuser can delete a business."},
                status=status.HTTP_403_FORBIDDEN
            )
        biz.delete()
        return Response({"message": f"{biz.name} deleted."})

    return Response(
        {"error": "Invalid action."},
        status=status.HTTP_400_BAD_REQUEST
    )


# ─────────────────────────────────────────────
# Reset user password
# ─────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdmin])
def reset_user_password(request, user_id):
    """Admin resets any user's password."""
    user = get_object_or_404(User, id=user_id)
    new_password = request.data.get("password")

    if not new_password or len(new_password) < 8:
        return Response(
            {"error": "Password must be at least 8 characters."},
            status=status.HTTP_400_BAD_REQUEST
        )

    user.set_password(new_password)
    user.save()
    return Response({"message": f"Password reset for {user.email}."})


# ─────────────────────────────────────────────
# Super Admin UI page
# ─────────────────────────────────────────────

def superadmin_page(request):
    return render(request, "superadmin.html")


# ─────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────

def _log(subscription, action, note, user):
    SubscriptionLog.objects.create(
        subscription=subscription,
        action=action,
        note=note,
        performed_by=user
    )