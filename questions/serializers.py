from rest_framework import serializers

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


class QuestionSerializer(serializers.ModelSerializer):
    """Base serializer for Question model."""

    class Meta:
        model = Question
        fields = [
            "id",
            "type",
            "difficulty",
            "jems",
            "xp_available",
            "explanation",
            "select_for_review",
        ]


class QuestionChoiceSerializer(serializers.ModelSerializer):
    """Serializer for question choices."""

    is_correct = serializers.SerializerMethodField()

    class Meta:
        model = QuestionChoice
        fields = ["id", "text", "is_correct", "order"]

    def get_is_correct(self, obj):
        """Only return is_correct for staff users."""
        request = self.context.get("request")
        if request and request.user.is_staff:
            return obj.is_correct
        return None


class MultipleChoiceQuestionSerializer(serializers.ModelSerializer):
    """Serializer for multiple choice questions."""

    choices = QuestionChoiceSerializer(many=True, read_only=True)
    correct_answers = serializers.SerializerMethodField()

    class Meta:
        model = MultipleChoiceQuestion
        fields = [
            "id",
            "type",
            "difficulty",
            "jems",
            "xp_available",
            "explanation",
            "select_for_review",
            "question_text",
            "is_multiple_selection",
            "choices",
            "correct_answers",
        ]
        read_only_fields = ["type", "correct_answers"]

    def get_correct_answers(self, obj):
        """Return list of correct choice IDs."""
        try:
            # Return correct answers only in admin context, not to regular users
            request = self.context.get("request")
            if request and request.user.is_staff:
                return obj.get_correct_choices()
        except Exception:
            pass
        return []


class FillBlankAnswerSerializer(serializers.ModelSerializer):
    """Serializer for fill blank answers."""

    class Meta:
        model = FillBlankAnswer
        fields = ["id", "blank_index", "text"]


class FillBlankQuestionSerializer(serializers.ModelSerializer):
    """Serializer for fill in the blank questions."""

    answers = serializers.SerializerMethodField()

    class Meta:
        model = FillBlankQuestion
        fields = [
            "id",
            "type",
            "difficulty",
            "jems",
            "explanation",
            "select_for_review",
            "question_text",
            "case_sensitive",
            "allow_typing",
            "answers",
        ]
        read_only_fields = ["type"]

    def get_answers(self, obj):
        """Return structured answers only for admin."""
        try:
            request = self.context.get("request")
            if request and request.user.is_staff:
                return obj.get_correct_answers()
        except Exception:
            pass
        return {}


class DragDropItemSerializer(serializers.ModelSerializer):
    """Serializer for drag drop items."""

    class Meta:
        model = DragDropItem
        fields = ["id", "text", "item_type", "order"]


class DragDropQuestionSerializer(serializers.ModelSerializer):
    """Serializer for drag and drop questions."""

    draggable_items = serializers.SerializerMethodField()
    drop_targets = serializers.SerializerMethodField()
    correct_mappings = serializers.SerializerMethodField()

    class Meta:
        model = DragDropQuestion
        fields = [
            "id",
            "type",
            "difficulty",
            "jems",
            "xp_available",
            "explanation",
            "select_for_review",
            "instructions",
            "draggable_items",
            "drop_targets",
            "correct_mappings",
        ]
        read_only_fields = ["type"]

    def get_draggable_items(self, obj):
        try:
            return obj.get_draggable_items()
        except Exception:
            return []

    def get_drop_targets(self, obj):
        try:
            return obj.get_drop_targets()
        except Exception:
            return []

    def get_correct_mappings(self, obj):
        """Return correct mappings only for admin."""
        try:
            request = self.context.get("request")
            if request and request.user.is_staff:
                return obj.get_correct_mappings()
        except Exception:
            pass
        return {}


class ReorderItemSerializer(serializers.ModelSerializer):
    """Serializer for reorder items."""

    class Meta:
        model = ReorderItem
        fields = ["id", "text"]


class ReorderQuestionSerializer(serializers.ModelSerializer):
    """Serializer for reorder questions."""

    items = serializers.SerializerMethodField()
    correct_order = serializers.SerializerMethodField()

    class Meta:
        model = ReorderQuestion
        fields = [
            "id",
            "type",
            "difficulty",
            "jems",
            "xp_available",
            "explanation",
            "select_for_review",
            "instructions",
            "items",
            "correct_order",
        ]
        read_only_fields = ["type"]

    def get_items(self, obj):
        try:
            return obj.get_items()
        except Exception:
            return []

    def get_correct_order(self, obj):
        """Return correct order only for admin."""
        try:
            request = self.context.get("request")
            if request and request.user.is_staff:
                return obj.get_correct_order()
        except Exception:
            pass
        return []


class QuestionSubmissionSerializer(serializers.Serializer):
    """Serializer for question submissions."""

    answer = serializers.JSONField()
    lesson = serializers.IntegerField()


class UserQuestionAttemptSerializer(serializers.ModelSerializer):
    """Serializer for UserQuestionAttempt model."""

    class Meta:
        model = UserQuestionAttempt
        fields = [
            "id",
            "question",
            "lesson",
            "user_answer",
            "is_correct",
            "jems_earned",
            "created_at",
        ]
        read_only_fields = ["is_correct", "jems_earned", "created_at"]
