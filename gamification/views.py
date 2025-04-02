from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Leaderboard
from .serializers import LeaderboardSerializer


class LeaderboardViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for leaderboard."""

    queryset = Leaderboard.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LeaderboardSerializer

    def get_queryset(self):
        period = self.request.query_params.get("period", "all_time")
        return Leaderboard.objects.filter(period=period).order_by("rank")[:100]

    @action(detail=False, methods=["get"])
    def my_rank(self, request):
        """Return the current user's rank on the leaderboard."""
        period = request.query_params.get("period", "all_time")
        try:
            entry = Leaderboard.objects.get(user=request.user, period=period)
            serializer = self.get_serializer(entry)
            return Response(serializer.data)
        except Leaderboard.DoesNotExist:
            return Response({"detail": "Not ranked yet."}, status=404)
