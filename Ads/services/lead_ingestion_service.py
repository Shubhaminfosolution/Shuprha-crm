import logging
from Leads.models import Lead
from Ads.models import AdForm

logger = logging.getLogger(__name__)


class LeadIngestionService:

    @staticmethod
    def parse_meta_data(field_data):
        data = {}
        for field in field_data:
            key = field["name"]
            value = field["values"][0]
            data[key] = value
        return data

    @staticmethod
    def create_lead_from_form(form_id, lead_data, platform):

        form = AdForm.objects.filter(form_id=form_id).first()
        if not form:
            logger.error(f"AdForm not found for form_id: {form_id}")
            return None

        business = form.account.business

        # ✅ Parse raw field_data from Meta
        parsed = LeadIngestionService.parse_meta_data(
            lead_data.get("field_data", [])
        )

        # ✅ Handle Meta field names correctly
        full_name = (
            parsed.get("full_name")
            or parsed.get("name")
            or ""
        ).strip()
        name_parts = full_name.strip().split(" ")
        first_name = name_parts[0] if name_parts else ""
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        phone = (
            parsed.get("phone_number")
            or parsed.get("phone")
            or ""
        )
        email = parsed.get("email", "")

        lead = Lead.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            source="meta ads",      # ← matches your Lead model choices
            source_platform=platform,
            business=business,
            ad_form=form,
            meta_lead_id=meta_lead_id,
        )
        logger.info(
            f"Lead created: {lead.id} | {lead.first_name} {lead.last_name} "
            f"| Business: {business.name}"
        )

        return lead







