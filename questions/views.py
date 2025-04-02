from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import timezone

from .models import (
    Question,
    MultipleChoiceQuestion,
    FillBlankQuestion,
    DragDropQuestion,
    ReorderQuestion,
    UserQuestionAttempt,
)
from .serializers import (
    QuestionSerializer,
    MultipleChoiceQuestionSerializer,
    FillBlankQuestionSerializer,
    DragDropQuestionSerializer,
    ReorderQuestionSerializer,
    QuestionSubmissionSerializer,
    UserQuestionAttemptSerializer,
)
from gamification.models import UserXP, UserJem
from users.models import CustomUser


class QuestionDetailView(generics.RetrieveAPIView):
    """View for retrieving a question."""

    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Override get_object to return the specialized question instance."""
        obj = super().get_object()

        # Get the specific question model instance based on type
        try:
            if obj.type == Question.QuestionType.MULTIPLE_CHOICE:
                return MultipleChoiceQuestion.objects.get(id=obj.id)
            elif obj.type == Question.QuestionType.FILL_BLANK:
                return FillBlankQuestion.objects.get(id=obj.id)
            elif obj.type == Question.QuestionType.DRAG_DROP:
                return DragDropQuestion.objects.get(id=obj.id)
            elif obj.type == Question.QuestionType.REORDER:
                return ReorderQuestion.objects.get(id=obj.id)
        except Exception:
            pass

        # Return the base question instance if specialized instance not found
        return obj

    def get_serializer_class(self):
        """Return the appropriate serializer based on question type."""
        try:
            question = self.get_object()

            if question.type == Question.QuestionType.MULTIPLE_CHOICE:
                return MultipleChoiceQuestionSerializer
            elif question.type == Question.QuestionType.FILL_BLANK:
                return FillBlankQuestionSerializer
            elif question.type == Question.QuestionType.DRAG_DROP:
                return DragDropQuestionSerializer
            elif question.type == Question.QuestionType.REORDER:
                return ReorderQuestionSerializer
        except Exception:
            pass

        # Fallback to base serializer
        return QuestionSerializer

    def get_serializer_context(self):
        """Add request to serializer context for permission checks."""
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to handle potential errors."""
        try:
            return super().retrieve(request, *args, **kwargs)
        except Exception as e:
            # Return more specific error if possible
            error_message = str(e)
            if "does not exist" in error_message:
                return Response(
                    {"detail": f"Question not found: {error_message}"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            return Response(
                {"detail": f"Error retrieving question: {error_message}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class QuestionSubmitView(generics.CreateAPIView):
    """View for submitting an answer to a question."""

    serializer_class = UserQuestionAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Handle question submission, evaluate answer, and update user stats."""
        # Get the question
        question_id = self.kwargs.get("pk")
        question = get_object_or_404(Question, id=question_id)

        # Validate submission data
        submission_serializer = QuestionSubmissionSerializer(data=request.data)
        if not submission_serializer.is_valid():
            return Response(
                submission_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        answer = submission_serializer.validated_data["answer"]
        lesson_id = submission_serializer.validated_data["lesson"]

        # Get the specific question instance based on type
        is_correct, feedback = self._evaluate_answer(question, answer)

        # Get attempt number
        attempt_count = UserQuestionAttempt.objects.filter(
            user=request.user, question=question, lesson_id=lesson_id
        ).count()

        # Calculate jems and XP earned (full points for first attempt, decreasing for subsequent attempts)
        jems_earned = 0
        xp_earned = 0

        if is_correct:
            if attempt_count == 0:
                # First correct attempt gets full points
                jems_earned = question.jems  # Use the jems value from the question
                xp_earned = (
                    question.xp_available
                )  # Use the xp_available from the question
            else:
                # Reduce rewards for subsequent attempts
                jems_earned = max(1, question.jems // (attempt_count + 1))
                xp_earned = max(10, question.xp_available // (attempt_count + 1))

        # Create attempt record
        attempt = UserQuestionAttempt.objects.create(
            user=request.user,
            question=question,
            lesson_id=lesson_id,
            user_answer=answer,
            is_correct=is_correct,
            attempt_number=attempt_count + 1,
            jems_earned=jems_earned,  # Use the calculated jems earned
        )

        # Update user gamification stats if correct
        if is_correct:
            user = request.user

            # Record XP transaction
            if xp_earned > 0:
                UserXP.objects.create(
                    user=user,
                    amount=xp_earned,
                    source_type=UserXP.SourceType.QUESTION,
                    content_type=ContentType.objects.get_for_model(question),
                    object_id=question.id,
                )

                # Update user total XP
                user.total_xp += xp_earned

            # Record Jem transaction
            if jems_earned > 0:
                UserJem.objects.create(
                    user=user,
                    amount=jems_earned,
                    source_type=UserJem.SourceType.QUESTION,
                    content_type=ContentType.objects.get_for_model(question),
                    object_id=question.id,
                )

                # Update user jems
                user.jems += jems_earned

            # Update last activity
            user.last_activity = timezone.now()

            # Save all user changes
            user.save(update_fields=["total_xp", "jems", "last_activity"])

            # Update streak (this would be more complex in reality)
            self._update_user_streak(user)

        # Return response with attempt details and gamification updates
        response_data = UserQuestionAttemptSerializer(attempt).data

        # Add additional response information
        response_data.update(
            {
                "feedback": feedback,
                "gamification_updates": {
                    "xp_earned": xp_earned,
                    "jems_earned": jems_earned,
                    "total_xp": request.user.total_xp,
                    "total_jems": request.user.jems,
                    "streak_days": request.user.streak_days,
                },
            }
        )

        return Response(response_data)

    def _evaluate_answer(self, question, answer):
        """Evaluate user's answer and return result and feedback."""
        if question.type == Question.QuestionType.MULTIPLE_CHOICE:
            specific_question = MultipleChoiceQuestion.objects.get(id=question.id)
            is_correct, feedback = self._validate_multiple_choice(
                specific_question, answer
            )
        elif question.type == Question.QuestionType.FILL_BLANK:
            specific_question = FillBlankQuestion.objects.get(id=question.id)
            is_correct, feedback = self._validate_fill_blank(specific_question, answer)
        elif question.type == Question.QuestionType.DRAG_DROP:
            specific_question = DragDropQuestion.objects.get(id=question.id)
            is_correct, feedback = self._validate_drag_drop(specific_question, answer)
        elif question.type == Question.QuestionType.REORDER:
            specific_question = ReorderQuestion.objects.get(id=question.id)
            is_correct, feedback = self._validate_reorder(specific_question, answer)
        else:
            return False, {"detail": "Unsupported question type."}

        return is_correct, feedback

    def _validate_multiple_choice(self, question, answer):
        """Validate multiple choice answer."""
        feedback = {"correct": False, "message": ""}

        if not isinstance(answer, list):
            feedback["message"] = "Answer must be a list of choice IDs"
            return False, feedback

        # For single selection, only one answer should be provided
        if not question.is_multiple_selection and len(answer) > 1:
            feedback["message"] = "Only one answer allowed for this question"
            return False, feedback

        # Convert answer to integers if they're strings
        try:
            answer = [int(a) for a in answer]
        except (ValueError, TypeError):
            feedback["message"] = "Invalid choice IDs"
            return False, feedback

        # Get correct answers from the question model
        correct_answers = question.get_correct_choices()

        # Check if the answers match
        is_correct = sorted(answer) == sorted(correct_answers)

        if is_correct:
            feedback["correct"] = True
            feedback["message"] = "Correct!"
            if question.explanation:
                feedback["explanation"] = question.explanation
        else:
            feedback["message"] = "Incorrect. Try again!"

        return is_correct, feedback

    def _validate_fill_blank(self, question, answer):
        """Validate fill in the blank answer."""
        feedback = {"correct": False, "message": ""}

        if not isinstance(answer, dict):
            feedback["message"] = (
                "Answer must be a dictionary mapping blank indices to answers"
            )
            return False, feedback

        # Get correct answers
        correct_answers = question.get_correct_answers()

        # Convert blank indices to strings for comparison
        answer = {str(k): v for k, v in answer.items()}
        print(correct_answers, answer)

        # Track incorrect blanks
        incorrect_blanks = []

        for blank_idx_str, user_answer in answer.items():
            try:
                blank_idx = int(blank_idx_str)
            except ValueError:
                feedback["message"] = f"Invalid blank index format: {blank_idx_str}"
                return False, feedback

            if blank_idx not in correct_answers:
                feedback["message"] = f"Invalid blank index: {blank_idx}"
                return False, feedback

            valid_answers = correct_answers[blank_idx]

            # Make sure it's a list
            if not isinstance(valid_answers, list):
                valid_answers = [valid_answers]

            # Check if answer is correct
            if question.case_sensitive:
                is_blank_correct = user_answer in valid_answers
            else:
                is_blank_correct = user_answer.lower() in [
                    a.lower() for a in valid_answers
                ]

            if not is_blank_correct:
                incorrect_blanks.append(blank_idx)

        # Overall result
        is_correct = len(incorrect_blanks) == 0

        if is_correct:
            feedback["correct"] = True
            feedback["message"] = "Correct!"
            if question.explanation:
                feedback["explanation"] = question.explanation
        else:
            feedback["message"] = "Incorrect. Try again!"
            feedback["incorrect_blanks"] = incorrect_blanks

        return is_correct, feedback

    def _validate_drag_drop(self, question, answer):
        """Validate drag and drop answer."""
        feedback = {"correct": False, "message": ""}

        if not isinstance(answer, dict):
            feedback["message"] = (
                "Answer must be a dictionary mapping target IDs to draggable item IDs"
            )
            return False, feedback

        # Get correct mappings
        correct_mappings = question.get_correct_mappings()
        # Convert indices to strings for comparison
        answer = {str(k): v for k, v in answer.items()}

        # Track incorrect mappings
        incorrect_targets = []

        for target_idx, item_indices in answer.items():
            if target_idx not in correct_mappings:
                feedback["message"] = f"Invalid target ID: {target_idx}"
                return False, feedback

            # Convert item indices to list if not already
            if not isinstance(item_indices, list):
                item_indices = [item_indices]

            # Convert to strings
            item_indices = [str(x) for x in item_indices]

            valid_items = correct_mappings[target_idx]

            # Make sure it's a list
            if not isinstance(valid_items, list):
                valid_items = [valid_items]

            # Check if all items are valid for this target
            for item_idx in item_indices:
                if item_idx not in valid_items:
                    incorrect_targets.append(target_idx)
                    break

        # Overall result
        is_correct = len(incorrect_targets) == 0

        if is_correct:
            feedback["correct"] = True
            feedback["message"] = "Correct!"
            if question.explanation:
                feedback["explanation"] = question.explanation
        else:
            feedback["message"] = "Incorrect. Try again!"
            feedback["incorrect_targets"] = incorrect_targets

        return is_correct, feedback

    def _validate_reorder(self, question, answer):
        """Validate reorder answer."""
        feedback = {"correct": False, "message": ""}

        if not isinstance(answer, list):
            feedback["message"] = (
                "Answer must be a list of item IDs in the correct order"
            )
            return False, feedback

        # Convert to strings for comparison
        answer = [str(x) for x in answer]

        # Get correct order
        correct_order = question.get_correct_order()

        # Compare with correct order
        is_correct = answer == correct_order

        if is_correct:
            feedback["correct"] = True
            feedback["message"] = "Correct sequence!"
            if question.explanation:
                feedback["explanation"] = question.explanation
        else:
            feedback["message"] = "Incorrect sequence. Try again!"

        return is_correct, feedback

    def _update_user_streak(self, user):
        """Update user streak based on activity."""
        if not user.last_activity:
            # First activity
            user.streak_days = 1
        else:
            # Get current date (in user's timezone ideally)
            today = timezone.localdate()
            last_activity_date = user.last_activity.date()

            # Check if last activity was yesterday
            if (today - last_activity_date).days == 1:
                user.streak_days += 1
            # If activity was today already, do nothing
            elif (today - last_activity_date).days > 1:
                # Streak broken
                user.streak_days = 1

        user.save(update_fields=["streak_days"])
