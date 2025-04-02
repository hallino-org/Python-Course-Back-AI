from django.urls import path, include, re_path
from rest_framework_nested import routers
from . import views
from lessons.views import LessonViewSet

app_name = "courses"

# Parent router for courses
router = routers.DefaultRouter()
router.register("", views.CourseViewSet, basename="course")

# Nested router for chapters within courses
chapters_router = routers.NestedDefaultRouter(router, "", lookup="course")
chapters_router.register("chapters", views.ChapterViewSet, basename="course-chapters")

# Nested router for prerequisites within courses
prerequisites_router = routers.NestedDefaultRouter(router, "", lookup="course")
prerequisites_router.register("prerequisites", views.CourseViewSet, basename="course-prerequisites")

# Nested router for lessons within courses
lessons_router = routers.NestedDefaultRouter(router, "", lookup="course")
lessons_router.register("lessons", LessonViewSet, basename="course-lessons")

# Nested router for enrollments within courses
enrollments_router = routers.NestedDefaultRouter(router, "", lookup="course")
enrollments_router.register(
    "enrollments", views.CourseEnrollmentViewSet, basename="course-enrollments"
)

urlpatterns = [
    # User enrolled courses endpoint (needs to be before router includes)
    path(
        "enrolled/",
        views.UserEnrolledCoursesView.as_view(),
        name="user-enrolled-courses",
    ),
    # Endpoint for enrolling in a course (supporting both slug and numeric ID)
    re_path(
        r"^(?P<slug>[\w-]+|[0-9]+)/enroll/$",
        views.CourseEnrollView.as_view(),
        name="course-enroll",
    ),
    # Include all router URLs
    path("", include(router.urls)),
    path("", include(chapters_router.urls)),
    path("", include(prerequisites_router.urls)),
    path("", include(lessons_router.urls)),
    path("", include(enrollments_router.urls)),
]
