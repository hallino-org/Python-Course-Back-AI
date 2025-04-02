from rest_framework import serializers

from .models import Course, UserCourseEnrollment, CoursePrerequisite
from categories.models import Category


class CourseSerializer(serializers.ModelSerializer):
    """Serializer for courses."""

    is_enrolled = serializers.SerializerMethodField()
    completion_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "estimated_time",
            "cover_image",
            "badge",
            "is_enrolled",
            "completion_percentage",
        ]

    def get_is_enrolled(self, obj):
        request = self.context.get("request")
        if request and hasattr(request, "user") and request.user.is_authenticated:
            return UserCourseEnrollment.objects.filter(
                user=request.user, course=obj
            ).exists()
        return False

    def get_completion_percentage(self, obj):
        request = self.context.get("request")
        if request and hasattr(request, "user") and request.user.is_authenticated:
            try:
                enrollment = UserCourseEnrollment.objects.get(
                    user=request.user, course=obj
                )
                return enrollment.completion_percentage
            except UserCourseEnrollment.DoesNotExist:
                pass
        return 0


class CourseDetailSerializer(CourseSerializer):
    """Detailed serializer for course information."""

    category = serializers.SlugRelatedField(
        slug_field="name", queryset=Category.objects.all()
    )
    prerequisites = serializers.SerializerMethodField()
    chapters_count = serializers.SerializerMethodField()
    lessons_count = serializers.SerializerMethodField()

    class Meta(CourseSerializer.Meta):
        fields = CourseSerializer.Meta.fields + [
            "category",
            "prerequisites",
            "chapters_count",
            "lessons_count",
            "created_at",
            "updated_at",
        ]

    def get_prerequisites(self, obj):
        """Get list of prerequisite courses."""
        prereqs = CoursePrerequisite.objects.filter(course=obj)
        return [
            {
                "id": prereq.prerequisite.id,
                "title": prereq.prerequisite.title,
                "slug": prereq.prerequisite.slug,
            }
            for prereq in prereqs
        ]

    def get_chapters_count(self, obj):
        """Get count of published chapters."""
        return obj.chapters.filter(is_published=True).count()

    def get_lessons_count(self, obj):
        """Get total count of published lessons across all chapters."""
        count = 0
        for chapter in obj.chapters.filter(is_published=True):
            count += chapter.lessons.filter(is_published=True).count()
        return count


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    """Serializer for course enrollments."""

    class Meta:
        model = UserCourseEnrollment
        fields = ["date_enrolled", "completion_percentage", "is_completed"]
        read_only_fields = ["date_enrolled", "completion_percentage", "is_completed"]
