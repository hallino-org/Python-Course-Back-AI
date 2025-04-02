from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'quests'

router = DefaultRouter()
router.register(r'quests', views.QuestViewSet, basename='quest')
router.register(r'tags', views.QuestTagViewSet, basename='quest-tag')
router.register(r'progress', views.UserQuestProgressViewSet, basename='quest-progress')
router.register(r'events', views.QuestEventViewSet, basename='quest-event')

urlpatterns = [
    path('', include(router.urls)),
] 