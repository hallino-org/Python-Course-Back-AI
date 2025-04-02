from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html

from .models import (
    Question,
    MultipleChoiceQuestion,
    FillBlankQuestion,
    DragDropQuestion,
    ReorderQuestion,
    UserQuestionAttempt,
    QuestionChoice,
    FillBlankAnswer,
    DragDropItem,
    DragDropMapping,
    ReorderItem,
)


class QuestionChoiceInline(admin.TabularInline):
    """Inline admin for question choices."""

    model = QuestionChoice
    extra = 2
    ordering = ["order"]
    classes = ["collapse"]
    fields = ["text", "is_correct", "order"]


class FillBlankAnswerInline(admin.TabularInline):
    """Inline admin for fill blank answers."""

    model = FillBlankAnswer
    extra = 1
    ordering = ["blank_index"]
    classes = ["collapse"]
    fields = ["blank_index", "text"]


class DragDropItemInline(admin.TabularInline):
    """Inline admin for drag drop items."""

    model = DragDropItem
    extra = 2
    ordering = ["item_type", "order"]
    classes = ["collapse"]
    fields = ["text", "item_type", "order"]


class DragDropMappingInline(admin.TabularInline):
    """Inline admin for drag drop mappings."""

    model = DragDropMapping
    extra = 1
    autocomplete_fields = ["target", "draggable_item"]
    classes = ["collapse"]
    verbose_name = "Correct Mapping"
    verbose_name_plural = "Correct Mappings"


class ReorderItemInline(admin.TabularInline):
    """Inline admin for reorder items."""

    model = ReorderItem
    extra = 3
    ordering = ["correct_position"]
    classes = ["collapse"]
    fields = ["text", "correct_position"]


class QuestionAdmin(admin.ModelAdmin):
    """Base admin for all question types with common functionality."""

    readonly_fields = ["type", "created_at", "updated_at"]
    save_on_top = True

    def get_fieldsets(self, request, obj=None):
        """Get fieldsets based on the question type."""
        return [
            (
                _("Question Content"),
                {
                    "fields": self.get_content_fields(),
                    "classes": ["wide"],
                },
            ),
            (
                _("Question Properties"),
                {
                    "fields": [
                        "difficulty",
                        "jems",
                        "explanation",
                        "select_for_review",
                    ],
                    "classes": ["collapse"],
                },
            ),
            (
                _("System Fields"),
                {
                    "fields": ["type", "created_at", "updated_at"],
                    "classes": ["collapse"],
                },
            ),
        ]

    def get_content_fields(self):
        """Method to be overridden by subclasses."""
        return []

    def get_question_type_display(self, obj):
        """Display question type with color-coding."""
        type_colors = {
            Question.QuestionType.MULTIPLE_CHOICE: "green",
            Question.QuestionType.FILL_BLANK: "blue",
            Question.QuestionType.DRAG_DROP: "purple",
            Question.QuestionType.REORDER: "red",
        }
        color = type_colors.get(obj.type, "gray")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_type_display(),
        )

    get_question_type_display.short_description = _("Type")
    get_question_type_display.admin_order_field = "type"


@admin.register(QuestionChoice)
class QuestionChoiceAdmin(admin.ModelAdmin):
    """Admin for QuestionChoice model."""

    list_display = ["id", "question", "text", "is_correct", "order"]
    list_filter = ["is_correct", "question"]
    search_fields = ["text", "question__question_text"]
    ordering = ["question", "order"]
    autocomplete_fields = ["question"]


@admin.register(FillBlankAnswer)
class FillBlankAnswerAdmin(admin.ModelAdmin):
    """Admin for FillBlankAnswer model."""

    list_display = ["id", "question", "blank_index", "text"]
    list_filter = ["blank_index", "question"]
    search_fields = ["text", "question__question_text"]
    ordering = ["question", "blank_index"]
    autocomplete_fields = ["question"]


@admin.register(DragDropItem)
class DragDropItemAdmin(admin.ModelAdmin):
    """Admin for DragDropItem model."""

    list_display = ["id", "get_question_text", "text", "item_type", "order"]
    list_filter = ["item_type", "question"]
    search_fields = ["text", "question__instructions"]
    ordering = ["question", "item_type", "order"]
    autocomplete_fields = ["question"]

    def get_question_text(self, obj):
        return (
            obj.question.instructions[:50] + "..."
            if len(obj.question.instructions) > 50
            else obj.question.instructions
        )

    get_question_text.short_description = _("Question")
    get_question_text.admin_order_field = "question__instructions"


@admin.register(DragDropMapping)
class DragDropMappingAdmin(admin.ModelAdmin):
    """Admin for DragDropMapping model."""

    list_display = ["id", "question", "target", "draggable_item"]
    list_filter = ["question"]
    search_fields = ["question__instructions", "target__text", "draggable_item__text"]
    autocomplete_fields = ["question", "target", "draggable_item"]


@admin.register(ReorderItem)
class ReorderItemAdmin(admin.ModelAdmin):
    """Admin for ReorderItem model."""

    list_display = ["id", "get_question_text", "text", "correct_position"]
    list_filter = ["question"]
    search_fields = ["text", "question__instructions"]
    ordering = ["question", "correct_position"]
    autocomplete_fields = ["question"]

    def get_question_text(self, obj):
        return (
            obj.question.instructions[:50] + "..."
            if len(obj.question.instructions) > 50
            else obj.question.instructions
        )

    get_question_text.short_description = _("Question")
    get_question_text.admin_order_field = "question__instructions"


@admin.register(MultipleChoiceQuestion)
class MultipleChoiceQuestionAdmin(QuestionAdmin):
    """Admin for MultipleChoiceQuestion model."""

    list_display = [
        "id",
        "question_text_display",
        "get_question_type_display",
        "is_multiple_selection",
        "difficulty",
        "jems",
        "get_choices_count",
    ]
    list_filter = ["difficulty", "is_multiple_selection", "select_for_review"]
    search_fields = ["question_text", "explanation"]
    inlines = [QuestionChoiceInline]
    autocomplete_fields = []

    def get_content_fields(self):
        return ["question_text", "is_multiple_selection"]

    def question_text_display(self, obj):
        return (
            obj.question_text[:50] + "..."
            if len(obj.question_text) > 50
            else obj.question_text
        )

    def get_choices_count(self, obj):
        return obj.choices.count()

    question_text_display.short_description = _("Question")
    get_choices_count.short_description = _("# Choices")
    question_text_display.admin_order_field = "question_text"


@admin.register(FillBlankQuestion)
class FillBlankQuestionAdmin(QuestionAdmin):
    """Admin for FillBlankQuestion model."""

    list_display = [
        "id",
        "question_text_display",
        "get_question_type_display",
        "case_sensitive",
        "allow_typing",
        "difficulty",
        "jems",
        "get_answers_count",
    ]
    list_filter = ["difficulty", "case_sensitive", "allow_typing", "select_for_review"]
    search_fields = ["question_text", "explanation"]
    inlines = [FillBlankAnswerInline]

    def get_content_fields(self):
        return ["question_text", "case_sensitive", "allow_typing"]

    def question_text_display(self, obj):
        return (
            obj.question_text[:50] + "..."
            if len(obj.question_text) > 50
            else obj.question_text
        )

    def get_answers_count(self, obj):
        return obj.answers.values("blank_index").distinct().count()

    question_text_display.short_description = _("Question")
    get_answers_count.short_description = _("# Blanks")
    question_text_display.admin_order_field = "question_text"


@admin.register(DragDropQuestion)
class DragDropQuestionAdmin(QuestionAdmin):
    """Admin for DragDropQuestion model."""

    list_display = [
        "id",
        "instructions_display",
        "get_question_type_display",
        "difficulty",
        "jems",
        "get_items_count",
    ]
    list_filter = ["difficulty", "select_for_review"]
    search_fields = ["instructions", "explanation"]
    inlines = [DragDropItemInline, DragDropMappingInline]

    def get_content_fields(self):
        return ["instructions"]

    def instructions_display(self, obj):
        return (
            obj.instructions[:50] + "..."
            if len(obj.instructions) > 50
            else obj.instructions
        )

    def get_items_count(self, obj):
        return f"{obj.items.filter(item_type='draggable').count()} draggable / {obj.items.filter(item_type='target').count()} targets"

    instructions_display.short_description = _("Instructions")
    get_items_count.short_description = _("Items")
    instructions_display.admin_order_field = "instructions"


@admin.register(ReorderQuestion)
class ReorderQuestionAdmin(QuestionAdmin):
    """Admin for ReorderQuestion model."""

    list_display = [
        "id",
        "instructions_display",
        "get_question_type_display",
        "difficulty",
        "jems",
        "get_items_count",
    ]
    list_filter = ["difficulty", "select_for_review"]
    search_fields = ["instructions", "explanation"]
    inlines = [ReorderItemInline]

    def get_content_fields(self):
        return ["instructions"]

    def instructions_display(self, obj):
        return (
            obj.instructions[:50] + "..."
            if len(obj.instructions) > 50
            else obj.instructions
        )

    def get_items_count(self, obj):
        return obj.reorder_items.count()

    instructions_display.short_description = _("Instructions")
    get_items_count.short_description = _("# Items")
    instructions_display.admin_order_field = "instructions"


@admin.register(UserQuestionAttempt)
class UserQuestionAttemptAdmin(admin.ModelAdmin):
    """Admin for UserQuestionAttempt model."""

    list_display = [
        "id",
        "user",
        "question",
        "lesson",
        "attempt_number",
        "is_correct",
        "jems_earned",
        "created_at",
    ]
    list_filter = ["is_correct", "attempt_number", "created_at"]
    search_fields = ["user__username", "user__email"]
    readonly_fields = ["user_answer", "created_at"]
    date_hierarchy = "created_at"
    ordering = ["-created_at"]

    def has_add_permission(self, request):
        return False


# Create a custom admin site
class QuestionAdminSite(admin.AdminSite):
    site_header = "Hallino Question Administration"
    site_title = "Hallino Question Admin"
    index_title = "Question Management"


# Initialize the question admin site
question_admin_site = QuestionAdminSite(name="question_admin")

# Register models with the custom admin site
question_admin_site.register(MultipleChoiceQuestion, MultipleChoiceQuestionAdmin)
question_admin_site.register(FillBlankQuestion, FillBlankQuestionAdmin)
question_admin_site.register(DragDropQuestion, DragDropQuestionAdmin)
question_admin_site.register(ReorderQuestion, ReorderQuestionAdmin)
question_admin_site.register(QuestionChoice, QuestionChoiceAdmin)
question_admin_site.register(FillBlankAnswer, FillBlankAnswerAdmin)
question_admin_site.register(DragDropItem, DragDropItemAdmin)
question_admin_site.register(DragDropMapping, DragDropMappingAdmin)
question_admin_site.register(ReorderItem, ReorderItemAdmin)
question_admin_site.register(UserQuestionAttempt, UserQuestionAttemptAdmin)
