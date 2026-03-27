from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.stories.api_v1.views import (
    StoryViewSet,
    AdminStoryViewSet,
    MessageThreadViewSet,
)

router = DefaultRouter()
router.register(r'stories', StoryViewSet, basename='story')
router.register(r'admin/stories', AdminStoryViewSet, basename='admin-story')
router.register(r'threads', MessageThreadViewSet, basename='thread')

app_name = 'stories_api_v1'

urlpatterns = [
    path('', include(router.urls)),
]
