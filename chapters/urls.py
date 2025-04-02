from django.urls import path, include
import re
from rest_framework_nested import routers
from . import views

app_name = "chapters"

# Parent router for chapters
router = routers.DefaultRouter()
router.register("", views.ChapterViewSet, basename="chapter")

# Nested router for lessons within chapters
lessons_router = routers.NestedDefaultRouter(router, "", lookup="chapter")
lessons_router.register("lessons", views.LessonViewSet, basename="chapter-lessons")

# Configure the router to accept both slugs and IDs
router.urls[0].pattern.regex = re.compile(r'^(?P<pk>[\w-]+|[0-9]+)/$')
lessons_router.urls[0].pattern.regex = re.compile(r'^(?P<chapter_pk>[\w-]+|[0-9]+)/lessons/$')

urlpatterns = [
    # Include all router URLs
    path("", include(router.urls)),
    path("", include(lessons_router.urls)),
]
