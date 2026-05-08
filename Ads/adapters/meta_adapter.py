import requests

class MetaAdapter:

    BASE_URL = "https://graph.facebook.com/v18.0"

    def __init__(self, access_token):
        self.access_token = access_token

    def get_lead(self, leadgen_id):  # ← rename from fetch_lead to get_lead

        url = f"{self.BASE_URL}/{leadgen_id}"  # ← remove /leads from URL

        params = {
            "access_token": self.access_token,
            "fields": "field_data"  # ← tell Meta which fields to return
        }

        response = requests.get(url, params=params)
        return response.json()