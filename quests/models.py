from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

class QuestTag(models.Model):
    """Tags that categorize quests and define their tracking behavior"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    tracking_type = models.CharField(
        max_length=20,
        choices=[
            ('counter', 'Counter (e.g., number of lessons completed)'),
            ('timer', 'Timer (e.g., time spent on platform)'),
            ('boolean', 'Boolean (e.g., achievement unlocked)'),
        ]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class Quest(models.Model):
    """Main quest model that defines quests and their requirements"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    quest_type = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Daily Quest'),
            ('weekly', 'Weekly Quest'),
            ('monthly', 'Monthly Quest'),
        ]
    )
    tags = models.ManyToManyField(QuestTag, related_name='quests')
    xp_reward = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="XP reward for completing this quest"
    )
    required_value = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Target value to achieve for quest completion"
    )
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    repeatable = models.BooleanField(
        default=True,
        help_text="Whether this quest can be completed multiple times"
    )
    prerequisites = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        related_name='dependent_quests',
        help_text="Quests that must be completed before this one becomes available"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_quest_type_display()}: {self.title}"

    def is_available(self, user):
        """Check if the quest is available for a user"""
        if not self.is_active:
            return False
        
        if self.end_date and timezone.now() > self.end_date:
            return False

        # Check prerequisites
        for prereq in self.prerequisites.all():
            if not UserQuestProgress.objects.filter(
                user=user,
                quest=prereq,
                is_completed=True
            ).exists():
                return False

        return True

class UserQuestProgress(models.Model):
    """Tracks user progress on quests"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE)
    current_value = models.PositiveIntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'quest']
        ordering = ['-last_updated']

    def __str__(self):
        return f"{self.user.username}'s progress on {self.quest.title}"

    def update_progress(self, value):
        """Update quest progress and check for completion"""
        self.current_value = value
        self.last_updated = timezone.now()

        if not self.is_completed and self.current_value >= self.quest.required_value:
            self.is_completed = True
            self.completed_at = timezone.now()
            # Award XP to user
            self.user.profile.add_xp(self.quest.xp_reward)

        self.save()

class QuestEvent(models.Model):
    """Tracks events that contribute to quest progress"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tag = models.ForeignKey(QuestTag, on_delete=models.CASCADE)
    value = models.PositiveIntegerField(default=1)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.tag.name} - {self.value}"

    def process(self):
        """Process the event and update relevant quest progress"""
        # Get all active quests with this tag
        active_quests = Quest.objects.filter(
            tags=self.tag,
            is_active=True,
            start_date__lte=timezone.now()
        )

        for quest in active_quests:
            if not quest.is_available(self.user):
                continue

            progress, created = UserQuestProgress.objects.get_or_create(
                user=self.user,
                quest=quest
            )

            if quest.repeatable or not progress.is_completed:
                if self.tag.tracking_type == 'counter':
                    progress.update_progress(progress.current_value + self.value)
                elif self.tag.tracking_type == 'timer':
                    progress.update_progress(progress.current_value + self.value)
                elif self.tag.tracking_type == 'boolean':
                    progress.update_progress(1)
