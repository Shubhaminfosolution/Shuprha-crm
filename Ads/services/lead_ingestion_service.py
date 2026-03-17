from Leads.models import Lead
from Ads.models import AdForm

class LeadIngestionService:
    @staticmethod
    def parse_meta_data(field_data):
        data ={}
        for field in field_data:
            key = field["name"]
            value = field["values"][0]
            data[key]=value
        return data

    @staticmethod
    def create_lead_from_form(form_id, lead_data, platform):

        form = AdForm.objects.filter(form_id=form_id).first()

        if not form:
            return None
        
        business = form.account.business

        parsed = LeadIngestionService.parse_meta_data(
            lead_data.get("field_data", [])
        )

        lead = Lead.objects.create(
            first_name = parsed.get("name"),
            email=parsed.get("email"),
            phone=parsed.get("phone"),
            source_platform = platform, 
            business=business,
            ad_form=form
            )

        return lead