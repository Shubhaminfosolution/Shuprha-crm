from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.http import HttpResponse
from .services.lead_ingestion_service import LeadIngestionService
from Ads.models import AdForm
from Ads.adapters.meta_adapter import MetaAdapter

VERIFY_TOKEN = "crm_verify_token"

@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def meta_webhook(request):

    if request.method == "GET":
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        print(f"GET received - mode: {mode}, token: {token}")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("✅ Verification successful")
            return HttpResponse(challenge)  # ← plain text

        print("❌ Verification failed")
        return HttpResponse(status=403)  # ← HttpResponse not Response

    if request.method == "POST":
        print("=" * 50)
        print("WEBHOOK POST RECEIVED")
        print("DATA:", request.data)
        print("=" * 50)

        entry = request.data.get("entry", [])

        for item in entry:
            changes = item.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                leadgen_id = value.get("leadgen_id")
                form_id = value.get("form_id")

                print(f"leadgen_id: {leadgen_id}, form_id: {form_id}")

                if leadgen_id and form_id:
                    form = AdForm.objects.filter(form_id=form_id).first()
                    print(f"Form found: {form}")

                    if not form:
                        print("❌ Form not found in DB")
                        continue

                    adapter = MetaAdapter(form.account.access_token)
                    lead_data = adapter.get_lead(leadgen_id)
                    print(f"Lead data: {lead_data}")

                    LeadIngestionService.create_lead_from_form(
                        form_id, lead_data, "meta"
                    )
                    print("✅ Lead created!")

        return Response({"status": "ok"})

    return HttpResponse(status=405)  # ← catch all other methods