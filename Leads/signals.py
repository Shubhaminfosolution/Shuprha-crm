from django.db.models.signals import post_save
from django.dispatch import receiver
from Leads.models import Lead
from Leads.tasks import send_whatsapp_messsage, send_appointment_reminder
from Leads.models import Appointment
from datetime import timedelta
from django.utils import timezone
from django.utils.timezone import localtime

@receiver(post_save, sender=Lead)
def lead_created(sender, instance, created, **kwargs):
    if created:
        message = (f"Hello {instance.first_name},\n\n"
                   "Thanks for contacting us! \n"
                   "We will reach out shortly.\n\n"
                   "- Team CRM")

        
        send_whatsapp_messsage.delay(instance.phone, message)



@receiver(post_save, sender=Appointment)
def schedule_reminder(sender, instance, created, **kwargs):
    if created:
        reminder_time = instance.date_time - timedelta(minutes=2)
        reminder_time = timezone.make_aware(reminder_time) if timezone.is_naive(reminder_time) else reminder_time
        print("scheduling reminder for: ", reminder_time)
        print("appointment id :", instance.id)
        send_appointment_reminder.apply_async(
            args=[instance.id],
            eta=reminder_time
        )


