from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "jems",
        "total_xp",
        "streak_days",
        "is_staff",
    )
    list_filter = ("role", "is_staff", "is_active", "is_superuser")
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email", "role")}),
        (
            _("Game Stats"),
            {
                "fields": (
                    "jems",
                    "total_xp",
                    "streak_days",
                    "last_activity",
                )
            },
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "password1",
                    "password2",
                    "first_name",
                    "last_name",
                    "role",
                ),
            },
        ),
    )
    search_fields = ("username", "email", "first_name", "last_name")


# We'll add UserBadgeAdmin back after migrations are complete
# class UserBadgeAdmin(admin.ModelAdmin):
#     list_display = ("user", "badge", "earned_date")
#     list_filter = ("badge", "earned_date")
#     search_fields = ("user__username", "badge__name")
#     date_hierarchy = "earned_date"


# admin.site.register(CustomUser, CustomUserAdmin)
# admin.site.register(UserBadge, UserBadgeAdmin)
