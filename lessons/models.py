from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class Lesson(models.Model):
    """Model representing a lesson within a chapter."""

    title = models.CharField(max_length=200, verbose_name=_("Title"))
    slug = models.SlugField(max_length=200, verbose_name=_("Slug"))
    chapter = models.ForeignKey(
        "chapters.Chapter",
        on_delete=models.CASCADE,
        related_name="lessons",
        verbose_name=_("Chapter"),
    )
    description = models.TextField(blank=True, verbose_name=_("Description"))
    order = models.PositiveIntegerField(default=1, verbose_name=_("Order"))
    estimated_time = models.PositiveIntegerField(
        help_text=_("Estimated completion time in minutes"),
        verbose_name=_("Estimated Time"),
    )
    xp_available = models.PositiveIntegerField(
        default=100, verbose_name=_("XP Available")
    )
    is_published = models.BooleanField(
        default=False, verbose_name=_("Is Published"))
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Lesson")
        verbose_name_plural = _("Lessons")
        ordering = ["chapter", "order"]
        unique_together = ["chapter", "slug"]

    def __str__(self):
        return f"{self.chapter.title} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class Slide(models.Model):
    """Model representing a slide within a lesson."""

    class SlideType(models.TextChoices):
        TEXT = 'text', _('Text Content')
        QUESTION = 'question', _('Question')

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='slides',
        verbose_name=_("Lesson"),
    )
    title = models.CharField(
        max_length=200, blank=True, verbose_name=_("Title"))
    type = models.CharField(
        max_length=20,
        choices=SlideType.choices,
        verbose_name=_("Type"),
    )
    order = models.PositiveIntegerField(default=0, verbose_name=_("Order"))

    # Common fields for all slide types
    is_required = models.BooleanField(
        default=True, verbose_name=_("Is Required"))
    completion_time = models.PositiveIntegerField(
        help_text=_("Estimated time in seconds"),
        default=60,
        verbose_name=_("Completion Time"),
    )

    # XP mechanism
    xp_available = models.PositiveIntegerField(
        default=10,
        verbose_name=_("XP Available"),
    )

    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        ordering = ['lesson', 'order']
        verbose_name = _("Slide")
        verbose_name_plural = _("Slides")

    def __str__(self):
        return f"{self.lesson.title} - Slide {self.order}: {self.get_type_display()}"


class CodeEditor(models.Model):
    """Model for code editor content in slides."""

    slide = models.OneToOneField(
        Slide,
        on_delete=models.CASCADE,
        related_name='code_editor',
        verbose_name=_("Slide"),
    )
    code_body = models.TextField(
        verbose_name=_("Code Content"),
        help_text=_("The actual code content to be displayed in the editor")
    )
    code_language = models.CharField(
        max_length=50,
        verbose_name=_("Programming Language"),
        help_text=_("The programming language for syntax highlighting")
    )
    runnable = models.BooleanField(
        default=False,
        verbose_name=_("Runnable"),
        help_text=_("Whether the code can be executed")
    )
    static_code = models.BooleanField(
        default=False,
        verbose_name=_("Static Code"),
        help_text=_("Whether the code is non-editable")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Code Editor")
        verbose_name_plural = _("Code Editors")
        ordering = ['-created_at']

    def __str__(self):
        return f"Code Editor ({self.code_language})"


class TextSlide(models.Model):
    """Model for text slide content."""

    slide = models.OneToOneField(
        Slide,
        on_delete=models.CASCADE,
        related_name='text_content',
        verbose_name=_("Slide"),
    )
    content = models.TextField(verbose_name=_("Content"))
    highlight = models.TextField(blank=True, verbose_name=_("Highlight Notes"))

    class Meta:
        verbose_name = _("Text Slide")
        verbose_name_plural = _("Text Slides")

    def __str__(self):
        return f"Text content for {self.slide}"


class QuestionSlide(models.Model):
    """Model for question slide content."""

    slide = models.OneToOneField(
        Slide,
        on_delete=models.CASCADE,
        related_name='question_content',
        verbose_name=_("Slide"),
    )
    question = models.ForeignKey(
        'questions.Question',
        on_delete=models.CASCADE,
        verbose_name=_("Question"),
    )
    is_for_review = models.BooleanField(
        default=False,
        verbose_name=_("Include in Review"),
        help_text=_("Include this question in lesson reviews"),
    )

    class Meta:
        verbose_name = _("Question Slide")
        verbose_name_plural = _("Question Slides")

    def __str__(self):
        return f"Question for {self.slide}"


class UserSlideProgress(models.Model):
    """Model to track user progress through slides."""

    user = models.ForeignKey(
        "users.CustomUser",
        on_delete=models.CASCADE,
        related_name="slide_progress",
        verbose_name=_("User"),
    )
    slide = models.ForeignKey(
        Slide,
        on_delete=models.CASCADE,
        related_name="user_progress",
        verbose_name=_("Slide"),
    )
    is_completed = models.BooleanField(
        default=False, verbose_name=_("Is Completed"))
    xp_earned = models.PositiveIntegerField(
        default=0, verbose_name=_("XP Earned"))
    completed_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Completed At"))
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        unique_together = ['user', 'slide']
        verbose_name = _("User Slide Progress")
        verbose_name_plural = _("User Slide Progress")

    def __str__(self):
        return f"{self.user.username} - {self.slide}"


class UserLessonProgress(models.Model):
    """Model to track user progress through lessons."""

    user = models.ForeignKey(
        "users.CustomUser",
        on_delete=models.CASCADE,
        related_name="lesson_progress",
        verbose_name=_("User"),
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="user_progress",
        verbose_name=_("Lesson"),
    )
    completion_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name=_("Completion Percentage"),
    )
    xp_earned = models.PositiveIntegerField(
        default=0, verbose_name=_("XP Earned"))
    current_slide = models.ForeignKey(
        Slide,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="progress_records",
        verbose_name=_("Current Slide"),
    )
    started_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Started At"))
    completed_date = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Completed Date")
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("User Lesson Progress")
        verbose_name_plural = _("User Lesson Progress")
        unique_together = ["user", "lesson"]

    def __str__(self):
        return f"{self.user.username} - {self.lesson.title} ({self.completion_percentage}%)"


class LessonReview(models.Model):
    """Model for lesson reviews."""

    user = models.ForeignKey(
        "users.CustomUser",
        on_delete=models.CASCADE,
        related_name="lesson_reviews",
        verbose_name=_("User"),
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name=_("Lesson"),
    )
    score = models.PositiveIntegerField(
        default=0, verbose_name=_("Review Score"))
    total_possible = models.PositiveIntegerField(
        default=0, verbose_name=_("Total Possible Score")
    )
    completion_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name=_("Completion Percentage"),
    )
    start_time = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Start Time"))
    completion_time = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Completion Time")
    )

    class Meta:
        verbose_name = _("Lesson Review")
        verbose_name_plural = _("Lesson Reviews")
        ordering = ["-start_time"]

    def __str__(self):
        return f"{self.user.username} - {self.lesson.title} Review ({self.completion_percentage}%)"


class LessonReviewQuestionAttempt(models.Model):
    """Model for tracking question attempts during a lesson review."""

    review = models.ForeignKey(
        LessonReview,
        on_delete=models.CASCADE,
        related_name="question_attempts",
        verbose_name=_("Review"),
    )
    question_slide = models.ForeignKey(
        QuestionSlide,
        on_delete=models.CASCADE,
        related_name="review_attempts",
        verbose_name=_("Question Slide"),
    )
    user_answer = models.JSONField(verbose_name=_("User Answer"))
    is_correct = models.BooleanField(verbose_name=_("Is Correct"))
    xp_earned = models.PositiveIntegerField(
        default=0, verbose_name=_("XP Earned"))
    attempt_time = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Attempt Time")
    )

    class Meta:
        verbose_name = _("Review Question Attempt")
        verbose_name_plural = _("Review Question Attempts")
        ordering = ["attempt_time"]

    def __str__(self):
        return f"{self.review.user.username} - {self.question_slide.question} Review Attempt"


class MediaFile(models.Model):
    """Model for media files attached to slides."""

    class MediaType(models.TextChoices):
        IMAGE = 'image', _('Image')
        VIDEO = 'video', _('Video')
        AUDIO = 'audio', _('Audio')
        DOCUMENT = 'document', _('Document')
        OTHER = 'other', _('Other')

    slide = models.ForeignKey(
        'Slide',
        on_delete=models.CASCADE,
        related_name='media_files',
        verbose_name=_("Slide"),
    )
    title = models.CharField(max_length=255, verbose_name=_("Title"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    file = models.FileField(
        upload_to='slides/media/%Y/%m/%d/',
        verbose_name=_("File"),
    )
    media_type = models.CharField(
        max_length=20,
        choices=MediaType.choices,
        default=MediaType.OTHER,
        verbose_name=_("Media Type"),
    )
    order = models.PositiveIntegerField(default=0, verbose_name=_("Order"))
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Updated At"))

    # Additional metadata
    file_size = models.PositiveIntegerField(
        blank=True,
        null=True,
        editable=False,
        verbose_name=_("File Size (bytes)"),
    )
    content_type = models.CharField(
        max_length=100,
        blank=True,
        editable=False,
        verbose_name=_("Content Type"),
    )

    class Meta:
        verbose_name = _("Media File")
        verbose_name_plural = _("Media Files")
        ordering = ['slide', 'order']

    def __str__(self):
        return f"{self.get_media_type_display()}: {self.title}"

    def save(self, *args, **kwargs):
        # Update file size if available
        if self.file and hasattr(self.file, 'size'):
            self.file_size = self.file.size

        # Try to determine media type from file extension if not set
        if not self.media_type or self.media_type == MediaFile.MediaType.OTHER:
            file_name = self.file.name.lower()
            if file_name.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp')):
                self.media_type = MediaFile.MediaType.IMAGE
            elif file_name.endswith(('.mp4', '.mov', '.avi', '.wmv', '.flv', '.webm', '.mkv')):
                self.media_type = MediaFile.MediaType.VIDEO
            elif file_name.endswith(('.mp3', '.wav', '.ogg', '.m4a', '.flac')):
                self.media_type = MediaFile.MediaType.AUDIO
            elif file_name.endswith(('.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt')):
                self.media_type = MediaFile.MediaType.DOCUMENT

        super().save(*args, **kwargs)

    @property
    def file_extension(self):
        """Return the file extension."""
        if self.file and hasattr(self.file, 'name'):
            import os
            return os.path.splitext(self.file.name)[1].lower()
        return ""

    @property
    def is_image(self):
        """Check if the file is an image."""
        return self.media_type == MediaFile.MediaType.IMAGE

    @property
    def is_video(self):
        """Check if the file is a video."""
        return self.media_type == MediaFile.MediaType.VIDEO
