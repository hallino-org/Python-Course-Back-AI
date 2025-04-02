from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import CourseRecommendation
from courses.models import Course
from courses.serializers import CourseSerializer


class CourseRecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for course recommendations."""

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CourseRecommendation.objects.filter(
            user=self.request.user, is_active=True
        ).order_by("-weight")

    def get_serializer_class(self):
        return CourseSerializer

    def list(self, request):
        queryset = self.get_queryset()
        recommended_courses = [rec.course for rec in queryset]
        serializer = self.get_serializer(recommended_courses, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def popular(self, request):
        """Return popular courses based on enrollment count."""
        popular_courses = Course.objects.filter(is_published=True).order_by(
            "-enrollment_count"
        )[:5]
        serializer = self.get_serializer(popular_courses, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def trending(self, request):
        """Return trending courses based on recent enrollment activity."""
        trending_courses = Course.objects.filter(is_published=True).order_by(
            "-recent_enrollment_count"
        )[:5]
        serializer = self.get_serializer(trending_courses, many=True)
        return Response(serializer.data)
