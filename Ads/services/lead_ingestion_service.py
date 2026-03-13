from Leads.models import Lead
from Ads.models import AdForm

class LeadIngestionService:

    @staticmethod
    def create_lead_from_form(form_id, data, platform):

        form = AdForm.objects.filter(form_id=form_id).first()

        if not form:
            return None
        
        business = form.account.business

        lead = Lead.objects.create(
            first_name = data.get("name"),
            email=data.get("email"),
            phone=data.get("phone"),
            source_platform = platform, 
            business=business,
            ad_form=form
            )

        return lead