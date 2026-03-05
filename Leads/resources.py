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
            "created_at",
        )