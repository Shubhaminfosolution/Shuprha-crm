from rest_framework.decorators import api_view
from rest_framework.response import Response
from .services.lead_ingestion_service import LeadIngestionService
from Ads.models import AdForm
from Ads.adapters.meta_adapter import MetaAdapter



@api_view(["POST"])
def meta_webhook(request):

    entry = request.data.get("entry", [])

    for item in entry:

        changes = item.get("changes", [])

        for change in changes:

            value = change.get("value", {})

            leadgen_id = value.get("leadgen_id")
            form_id = value.get("form_id")

            if leadgen_id and form_id:

                form = AdForm.objects.filter(form_id=form_id).first()

                if not form:
                    continue

                access_token = form.account.access_token

                adapter = MetaAdapter(access_token)

                lead_data = adapter.get_lead(leadgen_id)

                fields = lead_data.get("field_data", [])

                data = {}

                for field in fields:
                    data[field["name"]] = field["values"][0]

                LeadIngestionService.create_lead_from_form(
                    form_id,
                    data,
                    "meta"
                )

    return Response({"status": "ok"})




@api_view(["GET"])
def verify_meta(request):

    VERIFY_TOKEN = "crm_verify_token"

    mode = request.GET.get("hub.mode")
    token = request.GET.get("hub.verify_token")
    challenge = request.GET.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return Response(challenge)

    return Response(status=403)