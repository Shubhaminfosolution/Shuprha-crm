import urllib.parse 
from Leads.services.message_templates import get_default_message
def generate_whatsapp_link(first_name, phone):

    if not phone:
        return None
    
    phone = str(phone).replace("+", "").replace(" ", "")

    if not phone.startswith("91"):
        phone = f"91{phone}"

    message = get_default_message(first_name)
    encoded_message = urllib.parse.quote(message)

    return f"https://wa.me/{phone}?text={encoded_message}"



