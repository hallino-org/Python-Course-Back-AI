from django.urls import path, include
from rest_framework_nested import routers
from . import views

app_name = "users"

# Parent router for users
router = routers.DefaultRouter()
router.register("profile", views.UserProfileViewSet, basename="profile")

# Nested router for user progress
progress_router = routers.NestedDefaultRouter(router, "profile", lookup="user")
progress_router.register(
    "progress", views.UserProgressViewSet, basename="user-progress"
)

# Nested router for user achievements
achievements_router = routers.NestedDefaultRouter(router, "profile", lookup="user")
achievements_router.register(
    "achievements", views.UserAchievementsViewSet, basename="user-achievements"
)

urlpatterns = [
    path("register/", views.UserRegistrationView.as_view(), name="register"),
    path("me/", views.CurrentUserView.as_view(), name="me"),
    # Include all router URLs
    path("", include(router.urls)),
    path("", include(progress_router.urls)),
    path("", include(achievements_router.urls)),
]
