from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Chapter


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order", "is_published", "created_at")
    list_filter = ("course", "is_published")
    search_fields = ("title", "description", "course__title")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("title", "slug", "course", "description", "order")}),
        (_("Status"), {"fields": ("is_published", "created_at", "updated_at")}),
    )
    list_editable = ["order"]
