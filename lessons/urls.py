from django.urls import path, include
from rest_framework_nested import routers
from . import views

app_name = "lessons"

# Parent router for lessons
router = routers.DefaultRouter()
router.register("", views.LessonViewSet, basename="lesson")

# Nested router for slides within lessons
slides_router = routers.NestedDefaultRouter(router, "", lookup="lesson")
slides_router.register(
    "slides", views.SlideViewSet, basename="lesson-slides"
)

# Nested router for media files within slides
media_router = routers.NestedDefaultRouter(
    slides_router, "slides", lookup="slide")
media_router.register(
    "media", views.MediaFileViewSet, basename="slide-media"
)

# Nested router for slide progress within lessons
slide_progress_router = routers.NestedDefaultRouter(
    router, "", lookup="lesson")
slide_progress_router.register(
    "slide-progress", views.UserSlideProgressViewSet, basename="lesson-slide-progress"
)

# Nested router for slide progress within slides
# This nests as /lessons/{lesson_id}/slides/{slide_id}/progress/
slide_specific_progress_router = routers.NestedDefaultRouter(
    slides_router, "slides", lookup="slide"
)
slide_specific_progress_router.register(
    "progress", views.UserSlideProgressViewSet, basename="slide-progress"
)

# Nested router for lesson progress
progress_router = routers.NestedDefaultRouter(router, "", lookup="lesson")
progress_router.register(
    "progress", views.UserLessonProgressViewSet, basename="lesson-progress"
)

# Nested router for reviews within lessons
reviews_router = routers.NestedDefaultRouter(router, "", lookup="lesson")
reviews_router.register(
    "reviews", views.LessonReviewViewSet, basename="lesson-reviews")

# Nested router for questions within reviews
review_questions_router = routers.NestedDefaultRouter(
    reviews_router, "reviews", lookup="review"
)
review_questions_router.register(
    "questions", views.LessonReviewQuestionViewSet, basename="review-questions"
)

urlpatterns = [
    # Include all router URLs
    path("", include(router.urls)),
    path("", include(slides_router.urls)),
    path("", include(media_router.urls)),
    path("", include(slide_progress_router.urls)),
    path("", include(slide_specific_progress_router.urls)),
    path("", include(progress_router.urls)),
    path("", include(reviews_router.urls)),
    path("", include(review_questions_router.urls)),

    # Standalone endpoints
    path("<int:pk>/start/", views.LessonStartView.as_view(), name="lesson-start"),
    path("<int:pk>/complete/", views.LessonCompleteView.as_view(),
         name="lesson-complete"),
]
