from rest_framework import generics, viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from .models import CustomUser
from .serializers import UserSerializer, UserRegistrationSerializer


class UserRegistrationView(generics.CreateAPIView):
    """View for user registration."""

    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]


class CurrentUserView(generics.RetrieveAPIView):
    """View to retrieve the current authenticated user."""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        user = self.request.user
        user.last_activity = timezone.now()
        user.save(update_fields=["last_activity"])
        return user


# Custom permission to only allow admins to list all profiles
class IsAdminOrSelf(permissions.BasePermission):
    """
    Custom permission to only allow admins to list all profiles
    or users to view their own profile
    """

    def has_permission(self, request, view):
        # Allow admins to list all profiles
        if request.user.is_staff or request.user.role == "admin":
            return True

        # For list view, only allow admins
        if view.action == "list":
            return False

        # For retrieve, let has_object_permission handle it
        return True

    def has_object_permission(self, request, view, obj):
        # Allow admins to access any profile
        if request.user.is_staff or request.user.role == "admin":
            return True

        # Allow users to access their own profile
        return obj.id == request.user.id


class UserProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for user profiles."""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrSelf]

    def get_queryset(self):
        # Only admins can list all users
        if self.request.user.is_staff or self.request.user.role == "admin":
            return CustomUser.objects.filter(is_active=True)
        # Regular users can only see themselves
        return CustomUser.objects.filter(id=self.request.user.id, is_active=True)

    @action(detail=False, methods=["get"])
    def me(self, request):
        user = request.user
        user.last_activity = timezone.now()
        user.save(update_fields=["last_activity"])
        serializer = self.get_serializer(user)
        return Response(serializer.data)


class UserProgressViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for user progress across courses and lessons."""

    permission_classes = [permissions.IsAuthenticated, IsAdminOrSelf]

    def get_queryset(self):
        user_id = self.kwargs["user_pk"]
        if not self.request.user.is_staff and str(self.request.user.id) != user_id:
            raise PermissionDenied(
                "You do not have permission to view this user's progress"
            )

        # Get all progress records for the user
        from lessons.models import UserLessonProgress

        return UserLessonProgress.objects.filter(user_id=user_id).select_related(
            "lesson", "lesson__chapter", "lesson__chapter__course"
        )

    def get_serializer_class(self):
        from lessons.serializers import UserLessonProgressSerializer

        return UserLessonProgressSerializer


class UserAchievementsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for user achievements and badges."""

    permission_classes = [permissions.IsAuthenticated, IsAdminOrSelf]

    def get_queryset(self):
        user_id = self.kwargs["user_pk"]
        if not self.request.user.is_staff and str(self.request.user.id) != user_id:
            raise PermissionDenied(
                "You do not have permission to view this user's achievements"
            )

        # Get all XP transactions and badges for the user
        from gamification.models import UserXP

        return (
            UserXP.objects.filter(user_id=user_id)
            .select_related("content_type")
            .order_by("-created_at")
        )

    def get_serializer_class(self):
        from gamification.serializers import UserXPSerializer

        return UserXPSerializer
