from django.core.management.base import BaseCommand
from Ads.models import AdForm
from Ads.adapters.meta_adapter import MetaAdapter
from Ads.services.lead_ingestion_service import LeadIngestionService



class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        print("starting meta sync")
        forms = AdForm.objects.all()

        for form in forms:
            print(f"form:{form.form_id}")

            if not form.access_token:
                print("token skipped")
                continue

            adapter = MetaAdapter(form.access_token)

            data = adapter.fetch_leads(form.form_id)
            print("meta api")
        

            for lead in data.get("data", []):
                LeadIngestionService.create_lead_from_form(
                    form.form_id,
                    lead,
                    "META"
                )

        print("leads synced")