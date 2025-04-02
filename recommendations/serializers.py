from rest_framework import serializers
from .models import CourseRecommendation
from courses.serializers import CourseSerializer


class CourseRecommendationSerializer(serializers.ModelSerializer):
    """Serializer for CourseRecommendation model."""

    course = CourseSerializer(read_only=True)

    class Meta:
        model = CourseRecommendation
        fields = ["id", "course", "weight", "reason", "is_active"]
