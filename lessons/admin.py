from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html

from .models import (
    Lesson,
    Slide,
    TextSlide,
    QuestionSlide,
    UserSlideProgress,
    UserLessonProgress,
    LessonReview,
    LessonReviewQuestionAttempt,
    CodeEditor,
    MediaFile,
)


class TextSlideInline(admin.StackedInline):
    model = TextSlide
    extra = 0
    can_delete = False
    fields = ["content", "highlight"]


class QuestionSlideInline(admin.StackedInline):
    model = QuestionSlide
    extra = 0
    can_delete = False
    fields = ["question", "is_for_review"]


class CodeEditorInline(admin.StackedInline):
    """Inline admin for code editor content."""
    model = CodeEditor
    extra = 1
    max_num = 1
    can_delete = True
    fields = ['code_body', 'code_language', 'runnable', 'static_code']


class MediaFileInline(admin.TabularInline):
    """Inline admin for media files attached to slides."""
    model = MediaFile
    extra = 1
    fields = ['title', 'file', 'media_type', 'description', 'order']


@admin.register(CodeEditor)
class CodeEditorAdmin(admin.ModelAdmin):
    """Admin for CodeEditor model."""
    list_display = [
        'id',
        'slide',
        'code_language',
        'runnable',
        'static_code',
        'created_at',
        'updated_at',
    ]
    list_filter = ['code_language', 'runnable', 'static_code']
    search_fields = ['slide__title', 'slide__lesson__title', 'code_body']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        (None, {
            'fields': ['slide', 'code_body', 'code_language']
        }),
        (_('Editor Settings'), {
            'fields': ['runnable', 'static_code'],
            'classes': ['collapse']
        }),
        (_('Timestamps'), {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    )


@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    """Admin for MediaFile model."""
    list_display = [
        'id',
        'title',
        'slide',
        'media_type',
        'file_preview',
        'file_size_display',
        'order',
        'created_at',
    ]
    list_filter = ['media_type', 'created_at']
    search_fields = ['title', 'description',
                     'slide__title', 'slide__lesson__title']
    readonly_fields = ['file_preview', 'file_size_display',
                       'content_type', 'created_at', 'updated_at']
    fieldsets = (
        (None, {
            'fields': ['slide', 'title', 'description', 'file', 'media_type', 'order']
        }),
        (_('File Details'), {
            'fields': ['file_preview', 'file_size_display', 'content_type'],
            'classes': ['collapse']
        }),
        (_('Timestamps'), {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    )

    def file_preview(self, obj):
        """Display a preview of the file if it's an image."""
        if obj.is_image:
            return format_html('<img src="{}" width="100" height="auto" />', obj.file.url)
        elif obj.is_video:
            return format_html('<video width="100" height="auto" controls><source src="{}"></video>', obj.file.url)
        return format_html('<a href="{}" target="_blank">View File</a>', obj.file.url)
    file_preview.short_description = _("Preview")

    def file_size_display(self, obj):
        """Display file size in human-readable format."""
        if obj.file_size:
            # Convert to KB, MB, GB as appropriate
            size = obj.file_size
            if size < 1024:
                return f"{size} bytes"
            elif size < 1024 * 1024:
                return f"{size/1024:.1f} KB"
            elif size < 1024 * 1024 * 1024:
                return f"{size/(1024*1024):.1f} MB"
            else:
                return f"{size/(1024*1024*1024):.1f} GB"
        return "-"
    file_size_display.short_description = _("File Size")


@admin.register(Slide)
class SlideAdmin(admin.ModelAdmin):
    """Admin for Slide model."""
    list_display = [
        'id',
        'lesson',
        'title',
        'type',
        'order',
        'is_required',
        'completion_time',
        'xp_available',
        'has_code_editor',
        'media_count',
    ]
    list_filter = ['type', 'is_required', 'lesson']
    search_fields = ['title', 'lesson__title']
    ordering = ['lesson', 'order']
    inlines = [TextSlideInline, QuestionSlideInline,
               CodeEditorInline, MediaFileInline]
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "lesson",
                    "type",
                    "title",
                    "order",
                    "is_required",
                    "completion_time",
                    "xp_available",
                )
            },
        ),
        (_("Metadata"), {"fields": ("created_at", "updated_at")}),
    )
    list_editable = ["order"]

    def has_code_editor(self, obj):
        return hasattr(obj, 'code_editor') and bool(obj.code_editor)
    has_code_editor.boolean = True
    has_code_editor.short_description = _("Has Code Editor")

    def media_count(self, obj):
        return obj.media_files.count()
    media_count.short_description = _("Media Files")


class SlideInline(admin.TabularInline):
    model = Slide
    extra = 1
    fields = ["type", "order", "title", "is_required", "xp_available"]


class LessonReviewQuestionAttemptInline(admin.TabularInline):
    model = LessonReviewQuestionAttempt
    extra = 0
    readonly_fields = ["question_slide",
                       "is_correct", "xp_earned", "attempt_time"]
    can_delete = False
    max_num = 0
    fields = ["question_slide", "is_correct", "xp_earned", "attempt_time"]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "chapter",
        "order",
        "estimated_time",
        "xp_available",
        "is_published",
    ]
    list_filter = ["chapter__course", "chapter", "is_published"]
    search_fields = ["title", "chapter__title", "chapter__course__title"]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ["created_at", "updated_at"]
    inlines = [SlideInline]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "slug",
                    "chapter",
                    "order",
                    "estimated_time",
                    "xp_available",
                )
            },
        ),
        (_("Status"), {
         "fields": ("is_published", "created_at", "updated_at")}),
    )
    list_editable = ["order"]


@admin.register(UserLessonProgress)
class UserLessonProgressAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "lesson",
        "completion_percentage",
        "xp_earned",
        "started_at",
        "completed_date",
    ]
    list_filter = ["lesson__chapter__course", "lesson__chapter", "user"]
    search_fields = ["user__username", "lesson__title"]
    readonly_fields = ["started_at", "updated_at"]
    date_hierarchy = "started_at"


@admin.register(UserSlideProgress)
class UserSlideProgressAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "slide",
        "is_completed",
        "xp_earned",
        "completed_at",
    ]
    list_filter = ["slide__lesson__chapter__course",
                   "slide__lesson", "user", "is_completed"]
    search_fields = ["user__username", "slide__lesson__title"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "created_at"


@admin.register(LessonReview)
class LessonReviewAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "lesson",
        "score",
        "total_possible",
        "completion_percentage",
        "start_time",
        "completion_time",
    ]
    list_filter = ["lesson__chapter__course", "lesson__chapter", "user"]
    search_fields = ["user__username", "lesson__title"]
    readonly_fields = ["start_time"]
    date_hierarchy = "start_time"
    inlines = [LessonReviewQuestionAttemptInline]


@admin.register(LessonReviewQuestionAttempt)
class LessonReviewQuestionAttemptAdmin(admin.ModelAdmin):
    list_display = [
        "review",
        "question_slide",
        "is_correct",
        "xp_earned",
        "attempt_time",
    ]
    list_filter = ["review__lesson", "is_correct"]
    search_fields = ["review__user__username", "review__lesson__title"]
    readonly_fields = ["attempt_time"]
