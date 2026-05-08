import requests
from django.conf import settings

class WhatsAppSender:

    def send_message(self, phone, message):
        phone = str(phone).replace("+", "").replace(" ", "")
        if not phone.startswith("91"):
            phone = f"91{phone}"

            url = f"https://graph.facebook.com/v18.0/{settings.PHONE_NUMBER_ID}/messages"
            headers = {
                "Authorization":f"Bearer{settings.WHATSAPP_ACCESS_TOKEN}", 
                "Content-Type": "application/json"
            }
            data = {
                "messaging_product":"whatsapp",
                "to": phone,
                "type":"text",
                "text":{
                    "body": message
                }
            }

            response = requests.post(url, headers=headers, json=data)
            print("Whatsapp Response:", response.json())
            return response.json