import logging
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_meta_lead_task(self, leadgen_id: str, form_id: str):
    """
    Fetches lead data from Meta Graph API and creates a Lead in the DB.
    Retries up to 3 times with 60s delay if Meta API is slow.
    Deduplication: if meta_lead_id already exists, skips silently.
    """
    try:
        from Ads.models import AdForm
        from Ads.adapters.meta_adapter import MetaAdapter
        from Ads.services.lead_ingestion_service import LeadIngestionService
        from Leads.models import Lead

        # Deduplication check — webhook can fire twice for the same lead
        if Lead.objects.filter(meta_lead_id=leadgen_id).exists():
            logger.info(f"Duplicate webhook — lead {leadgen_id} already exists, skipping.")
            return

        form = AdForm.objects.filter(form_id=form_id).first()
        if not form:
            logger.error(f"No AdForm found for form_id: {form_id}")
            return

        adapter = MetaAdapter(form.account.access_token)
        lead_data = adapter.get_lead(leadgen_id)

        if "error" in lead_data:
            logger.error(f"Meta API error for lead {leadgen_id}: {lead_data['error']}")
            raise self.retry()

        lead = LeadIngestionService.create_lead_from_form(
            form_id, lead_data, "meta", meta_lead_id=leadgen_id
        )

        if lead:
            logger.info(f"Lead created: {lead.id} for business: {lead.business}")
            # Send email notification to business contact
            notify_new_lead_email.delay(lead.id)

    except Exception as exc:
        logger.exception(f"Error processing meta lead {leadgen_id}: {exc}")
        raise self.retry(exc=exc)


@shared_task
def notify_new_lead_email(lead_id: int):
    """
    Sends an email notification to the business contact email
    when a new lead arrives via Meta webhook.
    """
    try:
        from Leads.models import Lead

        lead = Lead.objects.select_related("business").get(id=lead_id)
        business = lead.business

        if not business or not business.contact_email:
            logger.warning(f"No business or contact email for lead {lead_id}, skipping email.")
            return

        subject = f"New lead received — {business.name}"
        message = (
            f"Hi {business.contact_person},\n\n"
            f"A new lead has just come in for {business.name}.\n\n"
            f"Name: {lead.first_name} {lead.last_name}\n"
            f"Phone: {lead.phone}\n"
            f"Email: {lead.email or 'Not provided'}\n"
            f"Source: {lead.source}\n\n"
            f"Log in to your dashboard to view and manage this lead.\n\n"
            f"— Shuprha CRM"
        )

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[business.contact_email],
            fail_silently=False,
        )

        logger.info(f"Email notification sent to {business.contact_email} for lead {lead_id}")

    except Exception as exc:
        logger.exception(f"Failed to send email for lead {lead_id}: {exc}")