from django.db import models
from django.conf import settings

class Activity(models.Model):

    ACTIVITY_TYPES = [
        ("call","Call"),
        ("email","Email"),
        ("meeting", "Meeting"),
        ("whatsapp","Whatsapp"),
        ("note", "Note"),
        ("followup", "Follow Up"),
    ]

    lead = models.ForeignKey(
        "Leads.lead",
        on_delete=models.CASCADE,
        related_name="activities"
    )

    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null =True,
        related_name="activated"
    )

    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    notes = models.TextField(blank=True)

    scheduled_at = models.DateTimeField(null=True, blank=True)
    completed = models.BooleanField(default=True)

    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes =[
            models.Index(fields=["activity_type"]),
            models.Index(fields=["scheduled_at"]),
            models.Index(fields=["completed"]),
            models.Index(fields=["created_at"]),
        ]
        ordering = ["-created_at"]

        def __str__(self):
            return f"{self.activity_type} - {self.lead.first_name}"



         