from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from categories.models import Category


class Course(models.Model):
    """Model representing a learning course."""

    BADGE_CHOICES = [
        ("new", "New"),
        ("popular", "Popular"),
        ("trending", "Trending"),
        ("bestseller", "Bestseller"),
        ("featured", "Featured"),
        ("none", "None"),
    ]

    title = models.CharField(max_length=255, verbose_name=_("Title"))
    slug = models.SlugField(
        max_length=255, unique=True, blank=True, verbose_name=_("Slug")
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="courses",
        verbose_name=_("Category"),
    )
    description = models.TextField(verbose_name=_("Description"))
    estimated_time = models.PositiveIntegerField(
        help_text=_("Estimated completion time in minutes"),
        verbose_name=_("Estimated Time"),
    )
    cover_image = models.ImageField(
        upload_to="course_covers/",
        blank=True,
        null=True,
        verbose_name=_("Cover Image"),
    )
    badge = models.CharField(
        max_length=20, choices=BADGE_CHOICES, default="none", verbose_name=_("Badge")
    )
    is_published = models.BooleanField(default=False, verbose_name=_("Is Published"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Course")
        verbose_name_plural = _("Courses")
        ordering = ["title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class CoursePrerequisite(models.Model):
    """Model for course prerequisites."""

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="prerequisites",
        verbose_name=_("Course"),
    )
    prerequisite = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="required_for",
        verbose_name=_("Prerequisite Course"),
    )

    class Meta:
        verbose_name = _("Course Prerequisite")
        verbose_name_plural = _("Course Prerequisites")
        unique_together = ["course", "prerequisite"]

    def __str__(self):
        return f"{self.course.title} requires {self.prerequisite.title}"


class UserCourseEnrollment(models.Model):
    """Model to track user enrollments in courses."""

    user = models.ForeignKey(
        "users.CustomUser",
        on_delete=models.CASCADE,
        related_name="enrollments",
        verbose_name=_("User"),
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="enrollments",
        verbose_name=_("Course"),
    )
    date_enrolled = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Date Enrolled")
    )
    completion_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name=_("Completion Percentage"),
    )
    is_completed = models.BooleanField(default=False, verbose_name=_("Is Completed"))

    class Meta:
        verbose_name = _("Course Enrollment")
        verbose_name_plural = _("Course Enrollments")
        unique_together = ["user", "course"]

    def __str__(self):
        return f"{self.user.username} enrolled in {self.course.title}"
