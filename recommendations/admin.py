from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import CourseRecommendation


@admin.register(CourseRecommendation)
class CourseRecommendationAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "relevance_score", "reason", "created_at")
    list_filter = ("reason", "created_at")
    search_fields = ("user__username", "course__title")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"
