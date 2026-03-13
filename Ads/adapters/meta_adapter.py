import requests

class MetaAdapter:

    BASE_URL = "https://graph.facebook.com/v18.0"

    def __init__(self, access_token):
        self.access_token = self.access_token

    def fetch_lead(self, leadgen_id):

        url = f"{self.BASE_URL}/{leadgen_id}"

        params = {
            "access_token":self.access_token
        }

        response = requests.get(url, params=params)
        return response.json()