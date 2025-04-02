from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import UserXP, UserJem, Leaderboard


@admin.register(UserXP)
class UserXPAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "source_type", "created_at")
    list_filter = ("source_type", "created_at")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"


@admin.register(UserJem)
class UserJemAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "source_type", "created_at")
    list_filter = ("source_type", "created_at")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"


@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ("user", "period", "xp", "rank", "updated_at")
    list_filter = ("period", "updated_at")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("updated_at",)
    date_hierarchy = "updated_at"
