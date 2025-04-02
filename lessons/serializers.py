from rest_framework import serializers

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
from questions.serializers import QuestionSerializer


class TextSlideSerializer(serializers.ModelSerializer):
    """Serializer for text slide content."""

    class Meta:
        model = TextSlide
        fields = [
            "id",
            "content",
            "highlight",
        ]


class QuestionSlideSerializer(serializers.ModelSerializer):
    """Serializer for question slide content."""

    question_data = serializers.SerializerMethodField()

    class Meta:
        model = QuestionSlide
        fields = [
            "id",
            "question",
            "question_data",
            "is_for_review",
        ]

    def get_question_data(self, obj):
        """Return the appropriate serialized question data based on type."""
        try:
            from questions.serializers import (
                QuestionSerializer,
                MultipleChoiceQuestionSerializer,
                FillBlankQuestionSerializer,
                DragDropQuestionSerializer,
                ReorderQuestionSerializer,
            )

            question = obj.question
            question_type = question.type

            # Use the appropriate serializer based on question type
            if question_type == "multiple_choice":
                return MultipleChoiceQuestionSerializer(
                    question.multiplechoicequestion, context=self.context
                ).data
            elif question_type == "fill_blank":
                return FillBlankQuestionSerializer(
                    question.fillblankquestion, context=self.context
                ).data
            elif question_type == "drag_drop":
                return DragDropQuestionSerializer(
                    question.dragdropquestion, context=self.context
                ).data
            elif question_type == "reorder":
                return ReorderQuestionSerializer(
                    question.reorderquestion, context=self.context
                ).data

            # Fallback to base serializer
            return QuestionSerializer(question, context=self.context).data

        except Exception:
            # Return minimal data to prevent 500
            return {"error": "Question details unavailable"}


class CodeEditorSerializer(serializers.ModelSerializer):
    """Serializer for code editor content."""
    class Meta:
        model = CodeEditor
        fields = ['id', 'code_body', 'code_language',
                  'runnable', 'static_code']


class MediaFileSerializer(serializers.ModelSerializer):
    """Serializer for media files attached to slides."""
    file_url = serializers.SerializerMethodField()
    file_size_formatted = serializers.SerializerMethodField()

    class Meta:
        model = MediaFile
        fields = [
            'id',
            'title',
            'description',
            'file',
            'file_url',
            'media_type',
            'order',
            'file_size',
            'file_size_formatted',
            'content_type',
            'file_extension',
            'created_at',
        ]
        read_only_fields = ['file_url', 'file_size', 'file_size_formatted',
                            'content_type', 'file_extension', 'created_at']

    def get_file_url(self, obj):
        """Get the absolute URL for the file."""
        request = self.context.get('request')
        if request and obj.file:
            return request.build_absolute_uri(obj.file.url)
        return None

    def get_file_size_formatted(self, obj):
        """Get the file size in a human-readable format."""
        if obj.file_size:
            size = obj.file_size
            if size < 1024:
                return f"{size} bytes"
            elif size < 1024 * 1024:
                return f"{size/1024:.1f} KB"
            elif size < 1024 * 1024 * 1024:
                return f"{size/(1024*1024):.1f} MB"
            else:
                return f"{size/(1024*1024*1024):.1f} GB"
        return None


class SlideSerializer(serializers.ModelSerializer):
    """Serializer for Slide model."""
    text_content = serializers.SerializerMethodField()
    question_content = serializers.SerializerMethodField()
    code_editor = CodeEditorSerializer(read_only=True)
    media_files = MediaFileSerializer(many=True, read_only=True)
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Slide
        fields = [
            'id',
            'lesson',
            'title',
            'type',
            'order',
            'is_required',
            'completion_time',
            'xp_available',
            'text_content',
            'question_content',
            'code_editor',
            'media_files',
            'progress',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_text_content(self, obj):
        """Get text content if slide is text type."""
        if obj.type == 'text':
            try:
                return TextSlideSerializer(obj.textslide).data
            except TextSlide.DoesNotExist:
                return None
        return None

    def get_question_content(self, obj):
        """Get question content if slide is question type."""
        if obj.type == 'question':
            try:
                return QuestionSlideSerializer(obj.questionslide).data
            except QuestionSlide.DoesNotExist:
                return None
        return None

    def get_progress(self, obj):
        """Get user's progress on this slide."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                progress = UserSlideProgress.objects.get(
                    user=request.user, slide=obj)
                return UserSlideProgressSerializer(progress).data
            except UserSlideProgress.DoesNotExist:
                return None
        return None


class UserSlideProgressSerializer(serializers.ModelSerializer):
    """Serializer for tracking user progress through slides."""

    class Meta:
        model = UserSlideProgress
        fields = [
            "id",
            "user",
            "slide",
            "is_completed",
            "xp_earned",
            "completed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["user", "slide", "created_at", "updated_at"]


class LessonSerializer(serializers.ModelSerializer):
    """Basic serializer for Lesson model."""

    class Meta:
        model = Lesson
        fields = [
            "id",
            "title",
            "slug",
            "chapter",
            "order",
            "estimated_time",
            "xp_available",
            "is_published",
        ]
        read_only_fields = ["slug"]


class UserLessonProgressSerializer(serializers.ModelSerializer):
    """Serializer for tracking user progress in lessons."""

    class Meta:
        model = UserLessonProgress
        fields = [
            "id",
            "user",
            "lesson",
            "completion_percentage",
            "xp_earned",
            "current_slide",
            "started_at",
            "completed_date",
            "updated_at",
        ]
        read_only_fields = ["user", "lesson", "started_at", "updated_at"]


class LessonDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for lessons with slides."""

    slides = SlideSerializer(many=True, read_only=True, source="slides.all")
    user_progress = serializers.SerializerMethodField()

    class Meta(LessonSerializer.Meta):
        fields = LessonSerializer.Meta.fields + ["slides", "user_progress"]

    def get_user_progress(self, obj):
        """Return user's progress for this lesson if authenticated."""
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            try:
                progress = UserLessonProgress.objects.get(
                    lesson=obj, user=request.user)
                return UserLessonProgressSerializer(progress).data
            except UserLessonProgress.DoesNotExist:
                return None
        return None


class LessonReviewQuestionAttemptSerializer(serializers.ModelSerializer):
    """Serializer for lesson review question attempts."""

    question_details = serializers.SerializerMethodField()

    class Meta:
        model = LessonReviewQuestionAttempt
        fields = [
            "id",
            "question_slide",
            "question_details",
            "user_answer",
            "is_correct",
            "xp_earned",
            "attempt_time",
        ]
        read_only_fields = ["attempt_time"]

    def get_question_details(self, obj):
        try:
            from questions.serializers import (
                QuestionSerializer,
                MultipleChoiceQuestionSerializer,
                FillBlankQuestionSerializer,
                DragDropQuestionSerializer,
                ReorderQuestionSerializer,
            )

            question = obj.question_slide.question
            question_type = question.type

            # Use the appropriate serializer based on question type
            if question_type == "multiple_choice":
                return MultipleChoiceQuestionSerializer(
                    question.multiplechoicequestion
                ).data
            elif question_type == "fill_blank":
                return FillBlankQuestionSerializer(question.fillblankquestion).data
            elif question_type == "drag_drop":
                return DragDropQuestionSerializer(question.dragdropquestion).data
            elif question_type == "reorder":
                return ReorderQuestionSerializer(question.reorderquestion).data

            # Fallback to base serializer
            return QuestionSerializer(question).data

        except Exception:
            # Return minimal data to prevent 500
            return {"error": "Question details unavailable"}


class LessonReviewSerializer(serializers.ModelSerializer):
    """Serializer for lesson reviews."""

    question_attempts = LessonReviewQuestionAttemptSerializer(
        many=True, read_only=True)

    class Meta:
        model = LessonReview
        fields = [
            "id",
            "lesson",
            "score",
            "total_possible",
            "completion_percentage",
            "start_time",
            "completion_time",
            "question_attempts",
        ]
        read_only_fields = [
            "start_time",
            "completion_time",
            "score",
            "total_possible",
            "completion_percentage",
        ]


class LessonReviewDetailSerializer(serializers.ModelSerializer):
    """Serializer for lesson review with attempts."""

    question_attempts = LessonReviewQuestionAttemptSerializer(
        many=True, read_only=True
    )

    class Meta:
        model = LessonReview
        fields = [
            "id",
            "user",
            "lesson",
            "score",
            "total_possible",
            "completion_percentage",
            "start_time",
            "completion_time",
            "question_attempts",
        ]
