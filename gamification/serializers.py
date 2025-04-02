from rest_framework import serializers
from .models import Leaderboard


class LeaderboardSerializer(serializers.ModelSerializer):
    """Serializer for Leaderboard model."""

    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Leaderboard
        fields = ["id", "period", "username", "xp", "rank", "updated_at"]
