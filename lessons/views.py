from rest_framework import viewsets, permissions, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import F, Count
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser

from .models import (
    Lesson,
    Slide,
    TextSlide,
    QuestionSlide,
    UserSlideProgress,
    UserLessonProgress,
    LessonReview,
    LessonReviewQuestionAttempt,
    MediaFile
)
from .serializers import (
    LessonSerializer,
    LessonDetailSerializer,
    SlideSerializer,
    TextSlideSerializer,
    QuestionSlideSerializer,
    UserSlideProgressSerializer,
    UserLessonProgressSerializer,
    LessonReviewSerializer,
    LessonReviewDetailSerializer,
    LessonReviewQuestionAttemptSerializer,
    MediaFileSerializer
)
from courses.models import UserCourseEnrollment
from gamification.models import UserXP
from questions.models import Question, UserQuestionAttempt
from questions.serializers import QuestionSubmissionSerializer


class LessonViewSet(viewsets.ModelViewSet):
    """ViewSet for lessons."""

    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Lesson.objects.filter(is_published=True)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return LessonDetailSerializer
        return LessonSerializer

    @action(detail=True, methods=['get'])
    def accuracy_stats(self, request, pk=None):
        """Get user's accuracy statistics for questions in this lesson."""
        lesson = self.get_object()

        # Get all question attempts for this lesson
        attempts = UserQuestionAttempt.objects.filter(
            user=request.user,
            lesson=lesson
        ).select_related('question')

        # Calculate statistics
        total_attempts = attempts.count()
        correct_attempts = attempts.filter(is_correct=True).count()

        # Calculate accuracy percentage
        accuracy_percentage = (
            correct_attempts / total_attempts * 100) if total_attempts > 0 else 0

        # Get course and chapter information
        course = lesson.chapter.course
        chapter = lesson.chapter

        # Get question type breakdown
        question_type_stats = attempts.values('question__type').annotate(
            total=Count('id'),
            correct=Count('id', filter=models.Q(is_correct=True))
        ).order_by('question__type')

        # Format question type statistics
        type_breakdown = {}
        for stat in question_type_stats:
            question_type = stat['question__type']
            total = stat['total']
            correct = stat['correct']
            type_breakdown[question_type] = {
                'total': total,
                'correct': correct,
                'accuracy': (correct / total * 100) if total > 0 else 0
            }

        response_data = {
            'lesson': {
                'id': lesson.id,
                'title': lesson.title,
                'chapter': {
                    'id': chapter.id,
                    'title': chapter.title
                },
                'course': {
                    'id': course.id,
                    'title': course.title
                }
            },
            'statistics': {
                'total_attempts': total_attempts,
                'correct_attempts': correct_attempts,
                'accuracy_percentage': round(accuracy_percentage, 2),
                'question_type_breakdown': type_breakdown
            }
        }

        return Response(response_data)


class SlideViewSet(viewsets.ModelViewSet):
    """ViewSet for slides."""

    serializer_class = SlideSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return slides for a specific lesson."""
        lesson_id = self.kwargs.get('lesson_pk')
        if lesson_id:
            return Slide.objects.filter(lesson_id=lesson_id).order_by('order')
        return Slide.objects.none()

    def perform_create(self, serializer):
        lesson = get_object_or_404(Lesson, id=self.kwargs["lesson_pk"])
        slide = serializer.save(lesson=lesson)

        # Create the appropriate type-specific content
        slide_type = serializer.validated_data.get('type')
        if slide_type == 'text':
            TextSlide.objects.create(slide=slide)
        elif slide_type == 'question':
            QuestionSlide.objects.create(slide=slide)

        return slide

    @action(detail=True, methods=["post"], url_path="update-content")
    def update_content(self, request, pk=None, lesson_pk=None):
        """Update the content of a slide based on its type."""
        slide = self.get_object()

        if slide.type == 'text':
            serializer = TextSlideSerializer(
                instance=getattr(slide, 'text_content', None),
                data=request.data
            )
            if serializer.is_valid():
                if not hasattr(slide, 'text_content'):
                    serializer.save(slide=slide)
                else:
                    serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif slide.type == 'question':
            serializer = QuestionSlideSerializer(
                instance=getattr(slide, 'question_content', None),
                data=request.data
            )
            if serializer.is_valid():
                if not hasattr(slide, 'question_content'):
                    serializer.save(slide=slide)
                else:
                    serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"detail": f"Unsupported slide type: {slide.type}"},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_media(self, request, pk=None, **kwargs):
        """Upload a media file to a slide."""
        slide = self.get_object()

        # Create a serializer with the request data
        serializer = MediaFileSerializer(
            data=request.data, context={'request': request})

        if serializer.is_valid():
            # Save the media file with the slide reference
            serializer.save(slide=slide)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def media(self, request, pk=None, **kwargs):
        """Get all media files for a slide."""
        slide = self.get_object()
        media_files = MediaFile.objects.filter(slide=slide).order_by('order')
        serializer = MediaFileSerializer(
            media_files, many=True, context={'request': request})
        return Response(serializer.data)


class UserSlideProgressViewSet(viewsets.ModelViewSet):
    """ViewSet for tracking user progress through slides."""

    serializer_class = UserSlideProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserSlideProgress.objects.filter(
            slide__lesson_id=self.kwargs["lesson_pk"],
            user=self.request.user
        )

    def perform_create(self, serializer):
        slide = get_object_or_404(
            Slide,
            id=self.kwargs.get("slide_pk"),
            lesson_id=self.kwargs["lesson_pk"]
        )
        # Check if progress already exists
        progress, created = UserSlideProgress.objects.get_or_create(
            slide=slide,
            user=self.request.user,
            defaults={"created_at": timezone.now()}
        )

        if not created:
            # Update existing progress
            serializer.instance = progress

        # Save progress
        serializer.save(user=self.request.user, slide=slide)

        # Update lesson progress
        self._update_lesson_progress(slide.lesson)

    def _update_lesson_progress(self, lesson):
        """Update the user's lesson progress based on slide completions."""
        # Get total required slides for this lesson
        total_slides = Slide.objects.filter(
            lesson=lesson,
            is_required=True
        ).count()

        if total_slides == 0:
            return

        # Get completed required slides
        completed_slides = UserSlideProgress.objects.filter(
            user=self.request.user,
            slide__lesson=lesson,
            slide__is_required=True,
            is_completed=True
        ).count()

        # Calculate completion percentage
        completion_percentage = (completed_slides / total_slides) * 100

        # Update or create lesson progress
        lesson_progress, _ = UserLessonProgress.objects.get_or_create(
            lesson=lesson,
            user=self.request.user,
            defaults={"started_at": timezone.now()}
        )

        # Update lesson progress
        lesson_progress.completion_percentage = completion_percentage

        # If completed, add completion date
        if completion_percentage >= 100 and not lesson_progress.completed_date:
            lesson_progress.completed_date = timezone.now()

            # Award XP for lesson completion if not already awarded
            if lesson_progress.xp_earned < lesson.xp_available:
                xp_to_award = lesson.xp_available - lesson_progress.xp_earned
                lesson_progress.xp_earned += xp_to_award

                # Create XP record
                UserXP.objects.create(
                    user=self.request.user,
                    amount=xp_to_award,
                    source_type="lesson",
                    content_type_id=None,  # Replace with proper ContentType for Lesson
                    object_id=lesson.id
                )

        lesson_progress.save()


class UserLessonProgressViewSet(viewsets.ModelViewSet):
    """ViewSet for tracking user progress in lessons."""

    serializer_class = UserLessonProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserLessonProgress.objects.filter(
            lesson_id=self.kwargs["lesson_pk"], user=self.request.user
        )

    def perform_create(self, serializer):
        lesson = get_object_or_404(Lesson, id=self.kwargs["lesson_pk"])
        # Check if progress already exists
        progress, created = UserLessonProgress.objects.get_or_create(
            lesson=lesson,
            user=self.request.user,
            defaults={"started_at": timezone.now()},
        )
        if not created:
            serializer.instance = progress
        serializer.save()

    @action(detail=True, methods=["post"], url_path="set-current-slide")
    def set_current_slide(self, request, pk=None, lesson_pk=None):
        """Set the current slide for the user's lesson progress."""
        progress = self.get_object()
        slide_id = request.data.get('slide_id')

        if not slide_id:
            return Response(
                {"detail": "slide_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            slide = Slide.objects.get(id=slide_id, lesson_id=lesson_pk)
        except Slide.DoesNotExist:
            return Response(
                {"detail": "Slide not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        progress.current_slide = slide
        progress.save()

        return Response(UserLessonProgressSerializer(progress).data)


class LessonReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for lesson reviews."""

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            QuestionSlide.objects.filter(
                slide__lesson_id=self.kwargs["lesson_pk"],
                is_for_review=True
            )
            .select_related("slide", "question")
            .order_by("?")[:5]
        )  # Random 5 questions

    def get_serializer_class(self):
        return QuestionSlideSerializer

    @action(detail=False, methods=["post"], url_path="start")
    def start_review(self, request, lesson_pk=None):
        """Start a new lesson review."""
        try:
            lesson = Lesson.objects.get(id=lesson_pk, is_published=True)
        except Lesson.DoesNotExist:
            return Response(
                {"detail": "Lesson not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Check if user has made enough progress
        try:
            progress = UserLessonProgress.objects.get(
                lesson=lesson,
                user=request.user
            )
            if progress.completion_percentage < 80:
                return Response(
                    {"detail": "You need to complete at least 80% of the lesson before reviewing"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except UserLessonProgress.DoesNotExist:
            return Response(
                {"detail": "You need to start the lesson before reviewing"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get review questions
        review_questions = QuestionSlide.objects.filter(
            slide__lesson=lesson,
            is_for_review=True
        ).select_related("slide", "question").order_by("?")[:5]

        if not review_questions:
            return Response(
                {"detail": "No review questions available for this lesson"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Create a new review
        review = LessonReview.objects.create(
            user=request.user,
            lesson=lesson,
            total_possible=len(review_questions)
        )

        return Response({
            "review_id": review.id,
            "questions": QuestionSlideSerializer(review_questions, many=True).data
        })


class LessonReviewQuestionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for questions within a lesson review."""

    serializer_class = LessonReviewQuestionAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        review_id = self.kwargs.get("review_pk")
        review = get_object_or_404(
            LessonReview, id=review_id, user=self.request.user)

        # Get all question attempts for this review
        return LessonReviewQuestionAttempt.objects.filter(review=review).select_related(
            "question_slide", "question_slide__question"
        )

    @action(detail=True, methods=["post"], url_path="submit")
    def submit_answer(self, request, pk=None, review_pk=None):
        """Submit an answer to a review question."""
        # Get the question slide
        question_slide = get_object_or_404(QuestionSlide, id=pk)

        # Get the review
        review = get_object_or_404(
            LessonReview,
            id=review_pk,
            user=request.user
        )

        # Validate submission
        submission_serializer = QuestionSubmissionSerializer(data=request.data)
        if not submission_serializer.is_valid():
            return Response(
                submission_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        user_answer = submission_serializer.validated_data.get("answer")

        # Check if correct using the question's validation logic
        question = question_slide.question
        is_correct = False

        if question.type == "multiple_choice":
            from questions.models import MultipleChoiceQuestion
            mcq = MultipleChoiceQuestion.objects.get(id=question.id)
            correct_choices = set(mcq.get_correct_choices())
            is_correct = set(user_answer) == correct_choices
        elif question.type == "fill_blank":
            from questions.models import FillBlankQuestion
            fbq = FillBlankQuestion.objects.get(id=question.id)
            correct_answers = fbq.get_correct_answers()
            is_correct = True
            for idx, answer in enumerate(user_answer):
                if idx not in correct_answers or answer.lower() not in [a.lower() for a in correct_answers[idx]]:
                    is_correct = False
                    break
        # Add other question types validation here

        # Calculate XP earned
        xp_earned = question.xp_available if is_correct else 0

        # Create the attempt record
        attempt = LessonReviewQuestionAttempt.objects.create(
            review=review,
            question_slide=question_slide,
            user_answer=user_answer,
            is_correct=is_correct,
            xp_earned=xp_earned
        )

        # Update review score
        if is_correct:
            review.score += 1

        # Calculate completion percentage
        total_attempts = LessonReviewQuestionAttempt.objects.filter(
            review=review).count()
        review.completion_percentage = (
            total_attempts / review.total_possible) * 100

        # If all questions answered, complete the review
        if total_attempts >= review.total_possible:
            review.completion_time = timezone.now()

            # Award XP if needed
            UserXP.objects.create(
                user=request.user,
                amount=xp_earned,
                source_type="review",
                content_type_id=None,  # Add proper ContentType
                object_id=review.id
            )

        review.save()

        return Response(LessonReviewQuestionAttemptSerializer(attempt).data)


class LessonStartView(generics.CreateAPIView):
    """View for starting a lesson."""

    serializer_class = UserLessonProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        lesson_id = self.kwargs.get("pk")
        try:
            lesson = Lesson.objects.get(pk=lesson_id, is_published=True)
        except Lesson.DoesNotExist:
            return Response(
                {"detail": "Lesson not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # Check if already in progress
        try:
            UserLessonProgress.objects.get(
                user=self.request.user, lesson=lesson)
            return Response(
                {"detail": "Lesson already in progress."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except UserLessonProgress.DoesNotExist:
            pass

        # Check if enrolled in course
        if not UserCourseEnrollment.objects.filter(
            user=self.request.user, course=lesson.chapter.course
        ).exists():
            return Response(
                {"detail": "You must be enrolled in this course to start this lesson."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get the first slide as the current_slide
        first_slide = Slide.objects.filter(
            lesson=lesson).order_by('order').first()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(
            user=self.request.user,
            lesson=lesson,
            completion_percentage=0,
            xp_earned=0,
            current_slide=first_slide
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LessonCompleteView(generics.UpdateAPIView):
    """View for completing a lesson."""

    serializer_class = UserLessonProgressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        lesson_id = self.kwargs.get("pk")
        try:
            lesson = Lesson.objects.get(pk=lesson_id, is_published=True)
        except Lesson.DoesNotExist:
            return Response(
                {"detail": "Lesson not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # Get user's progress for this lesson
        try:
            progress = UserLessonProgress.objects.get(
                user=self.request.user, lesson=lesson
            )
        except UserLessonProgress.DoesNotExist:
            return Response(
                {"detail": "You haven't started this lesson."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if all required slides are completed
        required_slides = Slide.objects.filter(
            lesson=lesson, is_required=True
        ).count()

        completed_slides = UserSlideProgress.objects.filter(
            user=self.request.user,
            slide__lesson=lesson,
            slide__is_required=True,
            is_completed=True
        ).count()

        if completed_slides < required_slides:
            return Response(
                {"detail": "You must complete all required slides before completing the lesson."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Mark as completed if not already
        if not progress.completed_date:
            progress.completed_date = timezone.now()
            progress.completion_percentage = 100

            # Award XP for lesson completion if not already awarded
            if progress.xp_earned < lesson.xp_available:
                xp_to_award = lesson.xp_available - progress.xp_earned
                progress.xp_earned += xp_to_award

                # Create XP record
                UserXP.objects.create(
                    user=self.request.user,
                    amount=xp_to_award,
                    source_type="lesson",
                    # ContentType.objects.get_for_model(Lesson).id,
                    content_type_id=None,
                    object_id=lesson.id,
                )

                # Update user's total XP
                self.request.user.total_xp = F("total_xp") + xp_to_award
                self.request.user.save(update_fields=["total_xp"])

            # Update course progress
            self._update_course_progress(lesson.chapter.course)

            progress.save()

        serializer = self.get_serializer(progress)
        return Response(serializer.data)

    def _update_course_progress(self, course):
        """Update the user's course progress."""
        try:
            enrollment = UserCourseEnrollment.objects.get(
                user=self.request.user, course=course
            )
        except UserCourseEnrollment.DoesNotExist:
            return

        # Calculate course completion percentage
        total_lessons = Lesson.objects.filter(
            chapter__course=course, is_published=True
        ).count()

        if total_lessons == 0:
            return

        completed_lessons = UserLessonProgress.objects.filter(
            user=self.request.user,
            lesson__chapter__course=course,
            completed_date__isnull=False,
        ).count()

        completion_percentage = (completed_lessons / total_lessons) * 100
        enrollment.completion_percentage = completion_percentage

        # Mark course as completed if all lessons are done
        if completion_percentage >= 100 and not enrollment.is_completed:
            enrollment.is_completed = True

            # Award XP for course completion
            course_xp = 500  # Base course completion XP
            UserXP.objects.create(
                user=self.request.user,
                amount=course_xp,
                source_type="course",
                # ContentType.objects.get_for_model(Course).id,
                content_type_id=None,
                object_id=course.id,
            )

            # Update user's total XP
            self.request.user.total_xp = F("total_xp") + course_xp
            self.request.user.save(update_fields=["total_xp"])

        enrollment.save()


class MediaFileViewSet(viewsets.ModelViewSet):
    """ViewSet for media files attached to slides."""
    serializer_class = MediaFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        """Return the media files for the specified slide."""
        slide_id = self.kwargs.get('slide_pk')
        if slide_id:
            return MediaFile.objects.filter(slide_id=slide_id).order_by('order')
        return MediaFile.objects.none()

    def perform_create(self, serializer):
        """Create a new media file for the specified slide."""
        slide_id = self.kwargs.get('slide_pk')
        slide = get_object_or_404(Slide, id=slide_id)
        serializer.save(slide=slide)
