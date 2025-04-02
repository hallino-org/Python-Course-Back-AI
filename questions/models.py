from django.db import models
from django.utils.translation import gettext_lazy as _


class Question(models.Model):
    """Base model for all question types."""

    class QuestionType(models.TextChoices):
        MULTIPLE_CHOICE = "multiple_choice", _("Multiple Choice")
        FILL_BLANK = "fill_blank", _("Fill in the Blank")
        DRAG_DROP = "drag_drop", _("Drag and Drop")
        REORDER = "reorder", _("Reorder")

    type = models.CharField(
        max_length=30, choices=QuestionType.choices, verbose_name=_("Type")
    )
    difficulty = models.PositiveSmallIntegerField(
        default=1,  # 1 = easy, 2 = medium, 3 = hard
        choices=[(1, _("Easy")), (2, _("Medium")), (3, _("Hard"))],
        verbose_name=_("Difficulty"),
    )
    jems = models.PositiveIntegerField(default=10, verbose_name=_("Jems"))
    xp_available = models.PositiveIntegerField(
        default=50, verbose_name=_("XP Available")
    )
    explanation = models.TextField(
        blank=True,
        help_text=_("Explanation shown after answering"),
        verbose_name=_("Explanation"),
    )
    select_for_review = models.BooleanField(
        default=False,
        verbose_name=_("Select for Review"),
        help_text=_("Include this question in lesson reviews"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Question")
        verbose_name_plural = _("Questions")

    def __str__(self):
        return f"{self.get_type_display()} ({self.id})"


class QuestionChoice(models.Model):
    """Model for question choices/options."""

    question = models.ForeignKey(
        "MultipleChoiceQuestion",
        on_delete=models.CASCADE,
        related_name="choices",
        verbose_name=_("Question"),
    )
    text = models.TextField(verbose_name=_("Choice Text"))
    is_correct = models.BooleanField(default=False, verbose_name=_("Is Correct"))
    order = models.PositiveIntegerField(default=0, verbose_name=_("Order"))

    class Meta:
        verbose_name = _("Question Choice")
        verbose_name_plural = _("Question Choices")
        ordering = ["order"]

    def __str__(self):
        return f"Choice for question {self.question.id}: {self.text[:30]}"


class MultipleChoiceQuestion(Question):
    """Model for multiple choice questions."""

    question_text = models.TextField(verbose_name=_("Question Text"))
    is_multiple_selection = models.BooleanField(
        default=False, verbose_name=_("Multiple Selection Allowed")
    )

    class Meta:
        verbose_name = _("Multiple Choice Question")
        verbose_name_plural = _("Multiple Choice Questions")

    def save(self, *args, **kwargs):
        self.type = Question.QuestionType.MULTIPLE_CHOICE
        super().save(*args, **kwargs)

    def get_correct_choices(self):
        """Return a list of IDs of correct choices."""
        return list(self.choices.filter(is_correct=True).values_list("id", flat=True))


class FillBlankAnswer(models.Model):
    """Model for fill in the blank acceptable answers."""

    question = models.ForeignKey(
        "FillBlankQuestion",
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name=_("Question"),
    )
    blank_index = models.PositiveIntegerField(verbose_name=_("Blank Index"))
    text = models.CharField(max_length=255, verbose_name=_("Answer Text"))

    class Meta:
        verbose_name = _("Fill Blank Answer")
        verbose_name_plural = _("Fill Blank Answers")
        ordering = ["blank_index"]

    def __str__(self):
        return f"Answer for question {self.question.id}, blank {self.blank_index}: {self.text}"


class FillBlankQuestion(Question):
    """Model for fill in the blank questions."""

    question_text = models.TextField(
        help_text=_("Use {blank} to indicate a blank"), verbose_name=_("Question Text")
    )
    case_sensitive = models.BooleanField(
        default=False, verbose_name=_("Case Sensitive")
    )
    allow_typing = models.BooleanField(
        default=True,
        verbose_name=_("Allow Typing"),
        help_text=_("If enabled, users can type their answers. If disabled, they must select from predefined options.")
    )

    class Meta:
        verbose_name = _("Fill in the Blank Question")
        verbose_name_plural = _("Fill in the Blank Questions")

    def save(self, *args, **kwargs):
        self.type = Question.QuestionType.FILL_BLANK
        super().save(*args, **kwargs)

    def get_correct_answers(self):
        """Return a dictionary of blank indices to lists of acceptable answers."""
        answers = {}
        for answer in self.answers.all():
            if answer.blank_index not in answers:
                answers[answer.blank_index] = []
            answers[answer.blank_index].append(answer.text)
        return answers


class DragDropItem(models.Model):
    """Model for drag and drop items."""

    question = models.ForeignKey(
        "DragDropQuestion",
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("Question"),
    )
    text = models.TextField(verbose_name=_("Item Text"))
    item_type = models.CharField(
        max_length=10,
        choices=[("draggable", _("Draggable")), ("target", _("Target"))],
        verbose_name=_("Item Type"),
    )
    order = models.PositiveIntegerField(default=0, verbose_name=_("Order"))

    class Meta:
        verbose_name = _("Drag Drop Item")
        verbose_name_plural = _("Drag Drop Items")
        ordering = ["item_type", "order"]

    def __str__(self):
        return f"{self.get_item_type_display()} for question {self.question.id}: {self.text[:30]}"


class DragDropMapping(models.Model):
    """Model for drag and drop correct mappings."""

    question = models.ForeignKey(
        "DragDropQuestion",
        on_delete=models.CASCADE,
        related_name="mappings",
        verbose_name=_("Question"),
    )
    target = models.ForeignKey(
        DragDropItem,
        on_delete=models.CASCADE,
        related_name="valid_items",
        verbose_name=_("Target"),
        limit_choices_to={"item_type": "target"},
    )
    draggable_item = models.ForeignKey(
        DragDropItem,
        on_delete=models.CASCADE,
        related_name="valid_targets",
        verbose_name=_("Draggable Item"),
        limit_choices_to={"item_type": "draggable"},
    )

    class Meta:
        verbose_name = _("Drag Drop Mapping")
        verbose_name_plural = _("Drag Drop Mappings")
        unique_together = ["target", "draggable_item"]

    def __str__(self):
        return f"Mapping for question {self.question.id}: {self.draggable_item.text[:20]} -> {self.target.text[:20]}"


class DragDropQuestion(Question):
    """Model for drag and drop questions."""

    instructions = models.TextField(verbose_name=_("Instructions"))

    class Meta:
        verbose_name = _("Drag and Drop Question")
        verbose_name_plural = _("Drag and Drop Questions")

    def save(self, *args, **kwargs):
        self.type = Question.QuestionType.DRAG_DROP
        super().save(*args, **kwargs)

    def get_draggable_items(self):
        """Return a list of draggable items."""
        return list(
            self.items.filter(item_type="draggable").values("id", "text", "order")
        )

    def get_drop_targets(self):
        """Return a list of drop targets."""
        return list(self.items.filter(item_type="target").values("id", "text", "order"))

    def get_correct_mappings(self):
        """Return a dictionary of target IDs to lists of valid draggable item IDs."""
        mappings = {}
        for mapping in self.mappings.all():
            target_id = str(mapping.target.id)
            if target_id not in mappings:
                mappings[target_id] = []
            mappings[target_id].append(str(mapping.draggable_item.id))
        return mappings


class ReorderItem(models.Model):
    """Model for reorder question items."""

    question = models.ForeignKey(
        "ReorderQuestion",
        on_delete=models.CASCADE,
        related_name="reorder_items",
        verbose_name=_("Question"),
    )
    text = models.TextField(verbose_name=_("Item Text"))
    correct_position = models.PositiveIntegerField(verbose_name=_("Correct Position"))

    class Meta:
        verbose_name = _("Reorder Item")
        verbose_name_plural = _("Reorder Items")
        ordering = ["correct_position"]

    def __str__(self):
        return f"Item for question {self.question.id}: position {self.correct_position}, {self.text[:30]}"


class ReorderQuestion(Question):
    """Model for reorder questions."""

    instructions = models.TextField(verbose_name=_("Instructions"))

    class Meta:
        verbose_name = _("Reorder Question")
        verbose_name_plural = _("Reorder Questions")

    def save(self, *args, **kwargs):
        self.type = Question.QuestionType.REORDER
        super().save(*args, **kwargs)

    def get_items(self):
        """Return a list of items to be reordered."""
        return list(self.reorder_items.values("id", "text"))

    def get_correct_order(self):
        """Return a list of item IDs in the correct order."""
        items = self.reorder_items.all().order_by("correct_position")
        return [str(item.id) for item in items]


class UserQuestionAttempt(models.Model):
    """Model to track user attempts at questions."""

    user = models.ForeignKey(
        "users.CustomUser",
        on_delete=models.CASCADE,
        related_name="question_attempts",
        verbose_name=_("User"),
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="attempts",
        verbose_name=_("Question"),
    )
    lesson = models.ForeignKey(
        "lessons.Lesson",
        on_delete=models.CASCADE,
        related_name="question_attempts",
        verbose_name=_("Lesson"),
    )
    user_answer = models.JSONField(verbose_name=_("User Answer"))
    is_correct = models.BooleanField(verbose_name=_("Is Correct"))
    attempt_number = models.PositiveIntegerField(
        default=1, verbose_name=_("Attempt Number")
    )
    jems_earned = models.PositiveIntegerField(default=0, verbose_name=_("Jems Earned"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        verbose_name = _("Question Attempt")
        verbose_name_plural = _("Question Attempts")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.question} (Attempt {self.attempt_number})"
