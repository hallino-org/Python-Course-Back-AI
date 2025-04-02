from rest_framework import serializers

from .models import Category


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for the Category model."""

    courses_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "icon", "courses_count"]

    def get_courses_count(self, obj):
        return obj.courses.filter(is_published=True).count()
