from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class CustomUser(AbstractUser):
    """Custom user model with additional fields for user profile."""

    class Role(models.TextChoices):
        STUDENT = "student", _("Student")
        TEACHER = "teacher", _("Teacher")
        ADMIN = "admin", _("Admin")

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.STUDENT,
        verbose_name=_("Role"),
    )
    jems = models.PositiveSmallIntegerField(default=5, verbose_name=_("Jems"))
    total_xp = models.PositiveIntegerField(default=0, verbose_name=_("Total XP"))
    streak_days = models.PositiveIntegerField(default=0, verbose_name=_("Streak Days"))
    last_activity = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Last Activity")
    )

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def __str__(self):
        return self.username


# We'll add UserBadge back after migrations are complete
