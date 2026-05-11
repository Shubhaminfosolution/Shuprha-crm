from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ("email", "full_name", "role", "business", "is_staff", "is_active")
    list_filter = ("role", "business", "is_staff", "is_active")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("full_name", "role", "business")}),
        ("Permissions", {"fields": ("is_staff", "is_superuser", "is_active", "groups", "user_permissions")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email", "full_name", "role", "business",
                "password1", "password2",
                "is_staff", "is_superuser"
            ),
        }),
    )

    search_fields = ("email", "full_name")
    ordering = ("email",)


admin.site.register(User, UserAdmin)