from django.urls import path, include
import re
from rest_framework_nested import routers

from . import views
from courses.views import CourseViewSet

app_name = "categories"

# Parent router for categories
router = routers.DefaultRouter()
router.register("", views.CategoryViewSet, basename="category")

# Nested router for courses within categories
courses_router = routers.NestedDefaultRouter(router, "", lookup="category")
courses_router.register("courses", CourseViewSet, basename="category-courses")

# Configure the router to accept both slugs and IDs
router.urls[0].pattern.regex = re.compile(r'^(?P<pk>[\w-]+|[0-9]+)/$')
courses_router.urls[0].pattern.regex = re.compile(r'^(?P<category_pk>[\w-]+|[0-9]+)/courses/$')

urlpatterns = [
    # Include all router URLs
    path("", include(router.urls)),
    path("", include(courses_router.urls)),
]
