from django.db.models.signals import post_save
from django.dispatch import receiver
from Leads.models import Lead, Appointment
from Leads.tasks import send_whatsapp_messsage, send_appointment_reminder
from Ads.tasks import notify_new_lead_email
from datetime import timedelta
from django.utils import timezone


@receiver(post_save, sender=Lead)
def lead_created(sender, instance, created, **kwargs):
    if created:
        # 1. WhatsApp message to the lead
        message = (
            f"Hello {instance.first_name},\n\n"
            "Thanks for contacting us!\n"
            "We will reach out shortly.\n\n"
            "- Team Shuprha"
        )
        send_whatsapp_messsage.delay(instance.phone, message)

        # 2. Email notification to the business contact
        # Only fires if lead belongs to a business (Meta leads always do)
        if instance.business_id:
            notify_new_lead_email.delay(instance.id)


@receiver(post_save, sender=Appointment)
def schedule_reminder(sender, instance, created, **kwargs):
    if created:
        reminder_time = instance.date_time - timedelta(minutes=30)
        reminder_time = (
            timezone.make_aware(reminder_time)
            if timezone.is_naive(reminder_time)
            else reminder_time
        )
        send_appointment_reminder.apply_async(
            args=[instance.id],
            eta=reminder_time
        )