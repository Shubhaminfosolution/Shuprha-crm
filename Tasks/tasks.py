import logging
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_task_reminder(self, task_id: int):
    """
    Sends email reminder to the assigned user 1 hour before task due date.
    Fires only once — reminder_sent flag prevents duplicates.
    """
    try:
        from Tasks.models import Task

        task = Task.objects.select_related(
            "assigned_to", "created_by"
        ).get(id=task_id)

        # Skip if already completed or reminder already sent
        if task.status == "completed" or task.reminder_sent:
            return

        assignee = task.assigned_to
        if not assignee.email:
            return

        subject = f"⏰ Task due in 1 hour — {task.title}"
        message = (
            f"Hi {assignee.full_name},\n\n"
            f"Your task is due in 1 hour.\n\n"
            f"Task: {task.title}\n"
            f"Priority: {task.priority.upper()}\n"
            f"Due: {task.due_date.strftime('%d %b %Y, %I:%M %p')}\n\n"
            f"{('Description: ' + task.description + chr(10) + chr(10)) if task.description else ''}"
            f"Log in to mark it complete.\n\n"
            f"— Shuprha CRM"
        )

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[assignee.email],
            fail_silently=False,
        )

        # Mark reminder sent
        Task.objects.filter(id=task_id).update(reminder_sent=True)
        logger.info(f"Task reminder sent to {assignee.email} for task {task_id}")

    except Exception as exc:
        logger.exception(f"Failed to send reminder for task {task_id}: {exc}")
        raise self.retry(exc=exc)


@shared_task
def mark_overdue_tasks():
    """
    Periodic task — runs every 30 minutes via Celery Beat.
    Automatically marks pending tasks as overdue if past due date.
    """
    from Tasks.models import Task

    now = timezone.now()
    updated = Task.objects.filter(
        status="pending",
        due_date__lt=now
    ).update(status="overdue")

    logger.info(f"Marked {updated} tasks as overdue.")
    return updated