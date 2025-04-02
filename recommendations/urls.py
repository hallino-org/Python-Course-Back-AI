from django.urls import path, include
import re
from rest_framework_nested import routers

from . import views  # Uncommented

app_name = "recommendations"

# Parent router for recommendations
router = routers.DefaultRouter()
router.register("courses", views.CourseRecommendationViewSet, basename="course_recommendation")

# Adding standalone endpoints for popular and trending
urlpatterns = [
    # Direct access to popular and trending
    path("courses/popular/", views.CourseRecommendationViewSet.as_view({'get': 'popular'}), name="popular-courses"),
    path("courses/trending/", views.CourseRecommendationViewSet.as_view({'get': 'trending'}), name="trending-courses"),
    
    # Include all router URLs
    path("", include(router.urls)),
]
