from rest_framework import serializers
from .models import Quest, QuestTag, UserQuestProgress, QuestEvent

class QuestTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestTag
        fields = ['id', 'name', 'description', 'tracking_type', 'is_active']

class QuestSerializer(serializers.ModelSerializer):
    tags = QuestTagSerializer(many=True, read_only=True)
    prerequisites = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    is_available = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Quest
        fields = [
            'id', 'title', 'description', 'quest_type', 'tags',
            'xp_reward', 'required_value', 'is_active', 'start_date',
            'end_date', 'repeatable', 'prerequisites', 'is_available',
            'progress'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_is_available(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.is_available(request.user)
        return False

    def get_progress(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                progress = UserQuestProgress.objects.get(user=request.user, quest=obj)
                return {
                    'current_value': progress.current_value,
                    'is_completed': progress.is_completed,
                    'completed_at': progress.completed_at
                }
            except UserQuestProgress.DoesNotExist:
                return {
                    'current_value': 0,
                    'is_completed': False,
                    'completed_at': None
                }
        return None

class UserQuestProgressSerializer(serializers.ModelSerializer):
    quest = QuestSerializer(read_only=True)

    class Meta:
        model = UserQuestProgress
        fields = ['id', 'quest', 'current_value', 'is_completed', 'completed_at', 'last_updated']
        read_only_fields = ['created_at', 'last_updated']

class QuestEventSerializer(serializers.ModelSerializer):
    tag = QuestTagSerializer(read_only=True)

    class Meta:
        model = QuestEvent
        fields = ['id', 'user', 'tag', 'value', 'metadata', 'created_at']
        read_only_fields = ['created_at']

    def create(self, validated_data):
        event = super().create(validated_data)
        event.process()  # Process the event to update quest progress 