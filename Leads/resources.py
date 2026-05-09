from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from Users.models import User
from .models import Lead

class LeadResource(resources.ModelResource):

    assigned_to = fields.Field(
        column_name="assigned_to",
        attribute="assigned_to",
        widget=ForeignKeyWidget(User, "email")
    )

    class Meta:
        model = Lead
        import_id_fields = ("email",)
        skip_unchanged = True
        report_skipped = True
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
            "phone",
            "status",
            "source",
            "assigned_to",
            "score",
            "notes",
        )

    STATUS_MAP = {
        "interested": "in progress",
        "not interested": "lost",
        "not answered": "not received",
        "not received": "not received",
        "busy": "busy",
        "callback": "in progress",
        "connected": "in progress",
        "invalid": "spam",
        "new": "new",
    }

    def before_import_row(self, row, **kwargs):
        # Split Name into first_name and last_name
        full_name = row.get("Name", "").strip()
        parts = full_name.split(" ", 1)
        row["first_name"] = parts[0] if parts else ""
        row["last_name"] = parts[1] if len(parts) > 1 else ""

        # Clean phone number
        phone = row.get("Phone number", "").strip()
        phone = phone.replace("p:", "").strip()
        phone = phone.replace("+91", "").replace(" ", "")[:12]
        row["phone"] = phone

        # Normalize status
        raw_status = row.get("Follow-up", "").strip().lower()
        row["status"] = self.STATUS_MAP.get(raw_status, "new")

        # Normalize source
        raw_source = row.get("DATA FROM", "").strip().lower()
        if "cold" in raw_source:
            row["source"] = "manual"
        else:
            row["source"] = "referral"

        # Notes
        row["notes"] = row.get("next followup", "")