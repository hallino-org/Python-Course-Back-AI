from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import Course, UserCourseEnrollment, CoursePrerequisite
from .serializers import (
    CourseSerializer,
    CourseEnrollmentSerializer,
    CourseDetailSerializer,
)
from chapters.serializers import ChapterSerializer
from lessons.serializers import LessonSerializer
from chapters.models import Chapter


class CourseViewSet(viewsets.ModelViewSet):
    """ViewSet for courses."""

    serializer_class = CourseSerializer
    lookup_field = 'slug'
    lookup_value_regex = '[\w-]+|[0-9]+'

    def get_queryset(self):
        return Course.objects.filter(is_published=True)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CourseDetailSerializer
        return CourseSerializer
        
    def get_object(self):
        """
        Returns the object the view is displaying.
        Supports both slug and primary key lookups.
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # Get the lookup value
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_value = self.kwargs[lookup_url_kwarg]
        
        # Try to determine if the lookup value is a primary key (integer)
        try:
            pk = int(lookup_value)
            obj = get_object_or_404(queryset, pk=pk)
        except (ValueError, TypeError):
            # If conversion to int fails, use the lookup_field (slug)
            filter_kwargs = {self.lookup_field: lookup_value}
            obj = get_object_or_404(queryset, **filter_kwargs)
            
        # May raise a permission denied
        self.check_object_permissions(self.request, obj)
        
        return obj


class ChapterViewSet(viewsets.ModelViewSet):
    """ViewSet for chapters within a course."""

    serializer_class = ChapterSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Chapter.objects.filter(
            course__slug=self.kwargs["course_slug"], is_published=True
        ).order_by("order")

    def perform_create(self, serializer):
        course = get_object_or_404(Course, slug=self.kwargs["course_slug"])
        serializer.save(course=course)


class CourseEnrollmentViewSet(viewsets.ModelViewSet):
    """ViewSet for course enrollments."""

    serializer_class = CourseEnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        course_lookup = self.kwargs["course_slug"]
        
        # Try to determine if the lookup value is a primary key (integer)
        try:
            course_id = int(course_lookup)
            return UserCourseEnrollment.objects.filter(course_id=course_id)
        except (ValueError, TypeError):
            # If conversion to int fails, assume it's a slug
            return UserCourseEnrollment.objects.filter(course__slug=course_lookup)

    def perform_create(self, serializer):
        course_lookup = self.kwargs["course_slug"]
        
        # Try to get the course by ID or slug
        try:
            course_id = int(course_lookup)
            course = get_object_or_404(Course, id=course_id)
        except (ValueError, TypeError):
            course = get_object_or_404(Course, slug=course_lookup)
            
        serializer.save(user=self.request.user, course=course)

    def get_object(self):
        queryset = self.get_queryset()
        return get_object_or_404(queryset, user=self.request.user)


class CourseEnrollView(generics.CreateAPIView):
    """View for enrolling in a course."""

    serializer_class = CourseEnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        course_slug = self.kwargs.get("slug")
        
        # Try to get the course by ID or slug
        try:
            course_id = int(course_slug)
            try:
                course = Course.objects.get(id=course_id, is_published=True)
            except Course.DoesNotExist:
                return Response(
                    {"detail": "Course not found."}, status=status.HTTP_404_NOT_FOUND
                )
        except (ValueError, TypeError):
            try:
                course = Course.objects.get(slug=course_slug, is_published=True)
            except Course.DoesNotExist:
                return Response(
                    {"detail": "Course not found."}, status=status.HTTP_404_NOT_FOUND
                )

        # Check if already enrolled
        if UserCourseEnrollment.objects.filter(
            user=self.request.user, course=course
        ).exists():
            return Response(
                {"detail": "Already enrolled in this course."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check prerequisites
        for prereq in course.prerequisites.all():
            try:
                enrollment = UserCourseEnrollment.objects.get(
                    user=self.request.user, course=prereq.prerequisite
                )
                if not enrollment.is_completed:
                    return Response(
                        {
                            "detail": f'Prerequisite course "{prereq.prerequisite.title}" must be completed first.'
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except UserCourseEnrollment.DoesNotExist:
                return Response(
                    {
                        "detail": f'Prerequisite course "{prereq.prerequisite.title}" must be completed first.'
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=self.request.user, course=course)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserEnrolledCoursesView(generics.ListAPIView):
    """View for listing all courses a user has enrolled in."""

    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Get all courses the user is enrolled in
        enrolled_course_ids = UserCourseEnrollment.objects.filter(
            user=self.request.user
        ).values_list("course_id", flat=True)

        return Course.objects.filter(id__in=enrolled_course_ids, is_published=True)
