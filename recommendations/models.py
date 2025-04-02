from django.db import models
from django.utils.translation import gettext_lazy as _


class CourseRecommendation(models.Model):
    """Model for storing course recommendations for users."""

    class RecommendationReason(models.TextChoices):
        PREREQUISITE_COMPLETED = "prerequisite_completed", _("Prerequisite Completed")
        SIMILAR_INTEREST = "similar_interest", _("Similar to Completed Courses")
        POPULAR = "popular", _("Popular in Category")
        NEXT_STEP = "next_step", _("Next Step in Learning Path")

    user = models.ForeignKey(
        "users.CustomUser",
        on_delete=models.CASCADE,
        related_name="recommended_courses",
        verbose_name=_("User"),
    )
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="recommended_to",
        verbose_name=_("Course"),
    )
    relevance_score = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name=_("Relevance Score")
    )
    reason = models.CharField(
        max_length=30, choices=RecommendationReason.choices, verbose_name=_("Reason")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        verbose_name = _("Course Recommendation")
        verbose_name_plural = _("Course Recommendations")
        unique_together = ["user", "course"]
        ordering = ["-relevance_score"]

    def __str__(self):
        return f"{self.course.title} recommendation for {self.user.username}"
