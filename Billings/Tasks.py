import logging
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

FOUNDER_EMAILS = [
    "admin@shuprha.com",       # you
    "premwaghmare88560@gmail.com",
    "sayali.karad08@gmail.com",
    "harshsurya1327@gmail.com",
]


@shared_task
def send_daily_report():
    """Sends daily summary to all 4 founders."""
    try:
        from Ads.models import Business
        from Leads.models import Lead
        from .models import Subscription

        today = timezone.now().date()
        yesterday = today - timedelta(days=1)

        new_businesses_today = Business.objects.filter(
            created_at__date=today
        ).count()

        new_leads_today = Lead.objects.filter(
            created_at__date=today,
            is_deleted=False
        ).count()

        total_mrr = sum(
            s.mrr for s in Subscription.objects.filter(status="active")
        )

        total_businesses = Business.objects.count()
        active_businesses = Subscription.objects.filter(status="active").count()

        subject = f"📊 Shuprha CRM — Daily Report {today.strftime('%d %b %Y')}"
        message = f"""
Good morning Team Shuprha! Here's your daily summary:

📅 DATE: {today.strftime('%d %B %Y')}

─────────────────────────────
🏢 BUSINESSES
─────────────────────────────
Total Businesses:     {total_businesses}
Active Subscriptions: {active_businesses}
New Today:            {new_businesses_today}

─────────────────────────────
📥 LEADS
─────────────────────────────
New Leads Today:      {new_leads_today}

─────────────────────────────
💰 REVENUE
─────────────────────────────
Current MRR:          ₹{total_mrr:,.0f}

─────────────────────────────

View full dashboard: https://crm.shuprha.com/superadmin/

— Shuprha CRM Auto Report
        """.strip()

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=FOUNDER_EMAILS,
            fail_silently=False,
        )
        logger.info("Daily report sent successfully.")

    except Exception as exc:
        logger.exception(f"Daily report failed: {exc}")


@shared_task
def send_weekly_report():
    """Sends weekly summary every Monday morning."""
    try:
        from Ads.models import Business
        from Leads.models import Lead
        from .models import Subscription

        today = timezone.now().date()
        week_start = today - timedelta(days=7)

        new_businesses_week = Business.objects.filter(
            created_at__date__gte=week_start
        ).count()

        new_leads_week = Lead.objects.filter(
            created_at__date__gte=week_start,
            is_deleted=False
        ).count()

        converted_week = Lead.objects.filter(
            updated_at__date__gte=week_start,
            status="converted",
            is_deleted=False
        ).count()

        total_mrr = sum(
            s.mrr for s in Subscription.objects.filter(status="active")
        )

        active = Subscription.objects.filter(status="active").count()
        suspended = Subscription.objects.filter(status="suspended").count()
        cancelled = Subscription.objects.filter(status="cancelled").count()

        # Top 5 businesses by leads this week
        top_businesses = []
        for biz in Business.objects.all():
            count = Lead.objects.filter(
                business=biz,
                created_at__date__gte=week_start,
                is_deleted=False
            ).count()
            if count > 0:
                top_businesses.append((biz.name, count))
        top_businesses.sort(key=lambda x: x[1], reverse=True)
        top_5 = top_businesses[:5]

        top_str = "\n".join(
            [f"  {i+1}. {name}: {count} leads"
             for i, (name, count) in enumerate(top_5)]
        ) or "  No leads this week"

        subject = f"📈 Shuprha CRM — Weekly Report ({week_start.strftime('%d %b')} – {today.strftime('%d %b %Y')})"
        message = f"""
Weekly Report — Team Shuprha

Period: {week_start.strftime('%d %B')} to {today.strftime('%d %B %Y')}

─────────────────────────────
🏢 BUSINESS GROWTH
─────────────────────────────
New Businesses This Week:  {new_businesses_week}
Active Subscriptions:      {active}
Suspended:                 {suspended}
Cancelled:                 {cancelled}

─────────────────────────────
📥 LEADS
─────────────────────────────
New Leads This Week:       {new_leads_week}
Converted This Week:       {converted_week}

─────────────────────────────
💰 REVENUE
─────────────────────────────
Current MRR:               ₹{total_mrr:,.0f}
Projected ARR:             ₹{total_mrr * 12:,.0f}

─────────────────────────────
🏆 TOP BUSINESSES BY LEADS
─────────────────────────────
{top_str}

─────────────────────────────

View full dashboard: https://crm.shuprha.com/superadmin/

— Shuprha CRM Auto Report
        """.strip()

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=FOUNDER_EMAILS,
            fail_silently=False,
        )
        logger.info("Weekly report sent successfully.")

    except Exception as exc:
        logger.exception(f"Weekly report failed: {exc}")