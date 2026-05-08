from celery import shared_task 
from Leads.services.whatsapp_sender import WhatsAppSender
from Leads.models import Appointment


@shared_task
def send_whatsapp_messsage(phone, message):
    sender = WhatsAppSender()
    sender.send_message(phone, message)

@shared_task
def send_appointment_reminder(appointment_id):
    try:
        appointment = Appointment.objects.get(id=appointment_id)
    except Appointment.DoesNotExist:
        print("Appointment {appointment_id} not found")
        return

    message = f"""
    
    Hi {appointment.lead.first_name},
    Your appointment is at {appointment.date_time.strftime('%d-%m-%Y %I:%M %p')}

    - Team CRM 

    """


    sender = WhatsAppSender()
    sender.send_message(appointment.lead.phone, message)