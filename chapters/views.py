from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Chapter
from lessons.models import Lesson
from .serializers import ChapterSerializer
from lessons.serializers import LessonSerializer


class ChapterViewSet(viewsets.ModelViewSet):
    """ViewSet for chapters."""

    serializer_class = ChapterSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_value_regex = '[\w-]+|[0-9]+'

    def get_queryset(self):
        return Chapter.objects.filter(is_published=True)
        
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
            # If the chapter has a slug field, we can look it up by slug
            if hasattr(queryset.model, 'slug'):
                obj = get_object_or_404(queryset, slug=lookup_value)
            else:
                raise
            
        # May raise a permission denied
        self.check_object_permissions(self.request, obj)
        
        return obj


class LessonViewSet(viewsets.ModelViewSet):
    """ViewSet for lessons within a chapter."""

    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        chapter_lookup = self.kwargs["chapter_pk"]
        
        # Try to determine if the lookup value is a primary key (integer)
        try:
            chapter_id = int(chapter_lookup)
            return Lesson.objects.filter(
                chapter_id=chapter_id, is_published=True
            ).order_by("order")
        except (ValueError, TypeError):
            # If conversion to int fails, assume it's a slug
            return Lesson.objects.filter(
                chapter__slug=chapter_lookup, is_published=True
            ).order_by("order")

    def perform_create(self, serializer):
        chapter_lookup = self.kwargs["chapter_pk"]
        
        # Try to get the chapter by ID or slug
        try:
            chapter_id = int(chapter_lookup)
            chapter = get_object_or_404(Chapter, id=chapter_id)
        except (ValueError, TypeError):
            chapter = get_object_or_404(Chapter, slug=chapter_lookup)
            
        serializer.save(chapter=chapter)
