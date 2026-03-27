from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.stories.api_v1.views import (
    StoryViewSet,
    AdminStoryViewSet,
    MessageThreadViewSet,
    HashtagViewSet,
)

router = DefaultRouter()
router.register(r'stories', StoryViewSet, basename='story')
router.register(r'admin/stories', AdminStoryViewSet, basename='admin-story')
router.register(r'threads', MessageThreadViewSet, basename='thread')
router.register(r'hashtags', HashtagViewSet, basename='hashtag')

app_name = 'stories_api_v1'

urlpatterns = [
    path('', include(router.urls)),
]
