from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from .models import Quest, QuestTag, UserQuestProgress, QuestEvent
from .serializers import (
    QuestSerializer, QuestTagSerializer,
    UserQuestProgressSerializer, QuestEventSerializer
)

# Create your views here.

class QuestViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = QuestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Quest.objects.filter(is_active=True)
        quest_type = self.request.query_params.get('type', None)
        tag = self.request.query_params.get('tag', None)
        available_only = self.request.query_params.get('available_only', None)

        if quest_type:
            queryset = queryset.filter(quest_type=quest_type)
        if tag:
            queryset = queryset.filter(tags__name=tag)
        if available_only:
            queryset = [q for q in queryset if q.is_available(self.request.user)]

        return queryset

    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get all available quests for the current user"""
        queryset = self.get_queryset()
        available_quests = [q for q in queryset if q.is_available(request.user)]
        serializer = self.get_serializer(available_quests, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def daily(self, request):
        """Get daily quests"""
        queryset = self.get_queryset().filter(quest_type='daily')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def weekly(self, request):
        """Get weekly quests"""
        queryset = self.get_queryset().filter(quest_type='weekly')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def monthly(self, request):
        """Get monthly quests"""
        queryset = self.get_queryset().filter(quest_type='monthly')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class QuestTagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = QuestTag.objects.filter(is_active=True)
    serializer_class = QuestTagSerializer
    permission_classes = [IsAuthenticated]

class UserQuestProgressViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserQuestProgressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserQuestProgress.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def completed(self, request):
        """Get completed quests"""
        queryset = self.get_queryset().filter(is_completed=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def in_progress(self, request):
        """Get in-progress quests"""
        queryset = self.get_queryset().filter(is_completed=False)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class QuestEventViewSet(viewsets.ModelViewSet):
    serializer_class = QuestEventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return QuestEvent.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def record_lesson_completion(self, request):
        """Record a lesson completion event"""
        try:
            tag = QuestTag.objects.get(name='lesson_completion')
            event = QuestEvent.objects.create(
                user=request.user,
                tag=tag,
                value=1,
                metadata={'lesson_id': request.data.get('lesson_id')}
            )
            event.process()
            return Response({'status': 'success'})
        except QuestTag.DoesNotExist:
            return Response(
                {'error': 'Quest tag not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'])
    def record_time_spent(self, request):
        """Record time spent on the platform"""
        try:
            tag = QuestTag.objects.get(name='time_spent')
            minutes = request.data.get('minutes', 1)
            event = QuestEvent.objects.create(
                user=request.user,
                tag=tag,
                value=minutes,
                metadata={'timestamp': timezone.now().isoformat()}
            )
            event.process()
            return Response({'status': 'success'})
        except QuestTag.DoesNotExist:
            return Response(
                {'error': 'Quest tag not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'])
    def record_correct_answers(self, request):
        """Record correct answers for questions"""
        try:
            tag = QuestTag.objects.get(name='correct_answers')
            count = request.data.get('count', 1)
            event = QuestEvent.objects.create(
                user=request.user,
                tag=tag,
                value=count,
                metadata={'lesson_id': request.data.get('lesson_id')}
            )
            event.process()
            return Response({'status': 'success'})
        except QuestTag.DoesNotExist:
            return Response(
                {'error': 'Quest tag not found'},
                status=status.HTTP_404_NOT_FOUND
            )
