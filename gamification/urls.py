from django.urls import path, include
from rest_framework_nested import routers

from . import views  # Uncommented

app_name = "gamification"

router = routers.DefaultRouter()
router.register("leaderboard", views.LeaderboardViewSet, basename="leaderboard")

urlpatterns = [
    # Include all router URLs
    path("", include(router.urls)),
]
