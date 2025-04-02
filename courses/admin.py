from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Course, CoursePrerequisite, UserCourseEnrollment


class CoursePrerequisiteInline(admin.TabularInline):
    model = CoursePrerequisite
    fk_name = "course"
    extra = 1
    verbose_name = _("Prerequisite")
    verbose_name_plural = _("Prerequisites")


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "estimated_time", "is_published", "created_at")
    list_filter = ("category", "is_published")
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")
    inlines = [CoursePrerequisiteInline]
    fieldsets = (
        (
            None,
            {"fields": ("title", "slug", "category", "description", "estimated_time")},
        ),
        (_("Media"), {"fields": ("cover_image",)}),
        (_("Badge"), {"fields": ("badge",)}),
        (_("Status"), {"fields": ("is_published", "created_at", "updated_at")}),
    )


@admin.register(UserCourseEnrollment)
class UserCourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "course",
        "date_enrolled",
        "completion_percentage",
        "is_completed",
    )
    list_filter = ("is_completed", "date_enrolled")
    search_fields = ("user__username", "course__title")
    readonly_fields = ("date_enrolled",)
    date_hierarchy = "date_enrolled"
