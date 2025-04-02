from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify


class Chapter(models.Model):
    """Model representing a chapter within a course."""

    title = models.CharField(max_length=200, verbose_name=_("Title"))
    slug = models.SlugField(max_length=200, verbose_name=_("Slug"))
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="chapters",
        verbose_name=_("Course"),
    )
    description = models.TextField(blank=True, verbose_name=_("Description"))
    order = models.PositiveIntegerField(default=1, verbose_name=_("Order"))
    is_published = models.BooleanField(default=False, verbose_name=_("Is Published"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Chapter")
        verbose_name_plural = _("Chapters")
        ordering = ["course", "order"]
        unique_together = ["course", "slug"]

    def __str__(self):
        return f"{self.course.title} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
