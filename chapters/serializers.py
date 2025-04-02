from rest_framework import serializers

from .models import Chapter


class ChapterSerializer(serializers.ModelSerializer):
    """Serializer for chapters."""

    lessons_count = serializers.SerializerMethodField()

    class Meta:
        model = Chapter
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "order",
            "lessons_count",
            "course",
        ]

    def get_lessons_count(self, obj):
        return obj.lessons.filter(is_published=True).count()
