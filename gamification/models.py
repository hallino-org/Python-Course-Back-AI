from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class UserXP(models.Model):
    """Model to track XP transactions for users."""

    class SourceType(models.TextChoices):
        LESSON = "lesson", _("Lesson Completion")
        QUESTION = "question", _("Question Correct")
        STREAK = "streak", _("Streak Bonus")
        COURSE = "course", _("Course Completion")
        ADMIN = "admin", _("Admin Adjustment")
        REVIEW = "review", _("Lesson Review")

    user = models.ForeignKey(
        "users.CustomUser",
        on_delete=models.CASCADE,
        related_name="xp_transactions",
        verbose_name=_("User"),
    )
    amount = models.IntegerField(verbose_name=_("Amount"))
    source_type = models.CharField(
        max_length=20, choices=SourceType.choices, verbose_name=_("Source Type")
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("Content Type"),
    )
    object_id = models.PositiveIntegerField(
        null=True, blank=True, verbose_name=_("Object ID")
    )
    reference_object = GenericForeignKey("content_type", "object_id")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        verbose_name = _("XP Transaction")
        verbose_name_plural = _("XP Transactions")
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.user.username}: {self.amount} XP ({self.get_source_type_display()})"
        )


class UserJem(models.Model):
    """Model to track Jem transactions for users."""

    class SourceType(models.TextChoices):
        QUESTION = "question", _("Question Correct")
        PURCHASE = "purchase", _("Shop Purchase")
        ADMIN = "admin", _("Admin Adjustment")
        QUEST = "quest", _("Quest Completion")

    user = models.ForeignKey(
        "users.CustomUser",
        on_delete=models.CASCADE,
        related_name="jem_transactions",
        verbose_name=_("User"),
    )
    amount = models.IntegerField(verbose_name=_("Amount"))
    source_type = models.CharField(
        max_length=20, choices=SourceType.choices, verbose_name=_("Source Type")
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("Content Type"),
    )
    object_id = models.PositiveIntegerField(
        null=True, blank=True, verbose_name=_("Object ID")
    )
    reference_object = GenericForeignKey("content_type", "object_id")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        verbose_name = _("Jem Transaction")
        verbose_name_plural = _("Jem Transactions")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username}: {self.amount} Jems ({self.get_source_type_display()})"


class Leaderboard(models.Model):
    """Model for caching leaderboard data."""

    class Period(models.TextChoices):
        DAILY = "daily", _("Daily")
        WEEKLY = "weekly", _("Weekly")
        MONTHLY = "monthly", _("Monthly")
        ALL_TIME = "all_time", _("All Time")

    period = models.CharField(
        max_length=20, choices=Period.choices, verbose_name=_("Time Period")
    )
    user = models.ForeignKey(
        "users.CustomUser",
        on_delete=models.CASCADE,
        related_name="leaderboard_entries",
        verbose_name=_("User"),
    )
    xp = models.PositiveIntegerField(verbose_name=_("XP"), default=0)
    rank = models.PositiveIntegerField(verbose_name=_("Rank"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Last Updated"))

    class Meta:
        verbose_name = _("Leaderboard Entry")
        verbose_name_plural = _("Leaderboard Entries")
        unique_together = ["period", "user"]
        ordering = ["period", "rank"]

    def __str__(self):
        return f"{self.user.username} - {self.get_period_display()} - Rank {self.rank}"
