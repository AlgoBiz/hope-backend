from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.stories.models import Story, MessageThread, Message, Hashtag
from apps.stories.service import increment_view_count, get_or_create_thread
from apps.stories.api_v1.permissions import IsAdminUser, IsOwnerOrAdmin
from apps.stories.api_v1.serializers import (
    StorySerializer, AdminStorySerializer, StoryActionSerializer,
    StoryMediaUploadSerializer, StoryDocumentUploadSerializer,
    MessageSerializer, MessageThreadDetailSerializer, MessageThreadListSerializer,
    HashtagSerializer,
)
from apps.user_account.utils import success_response, error_response



class StoryViewSet(viewsets.ModelViewSet):
    serializer_class = StorySerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'related'):
            return [AllowAny()]
        if self.action in ('update', 'partial_update', 'destroy', 'submit', 'upload_media', 'upload_document'):
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = (
            Story.objects
            .select_related('user')
            .prefetch_related('hashtags', 'media', 'documents')
        )
        if self.action == 'list':
            qs = qs.filter(status=Story.Status.APPROVED)
            hashtag = self.request.query_params.get('hashtag')
            if hashtag:
                qs = qs.filter(hashtags__name__iexact=hashtag).distinct()
        elif self.action == 'my':
            qs = qs.filter(user=self.request.user)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        # Public — every visit (auth or anonymous) increments view_count
        story = self.get_object()
        increment_view_count(story)
        story.refresh_from_db(fields=['view_count'])
        return success_response(data=self.get_serializer(story).data)

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return success_response(data=self.get_serializer(qs, many=True).data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return error_response(errors=serializer.errors, message="Story creation failed.")
        self.perform_create(serializer)
        return success_response(data=serializer.data, message="Story created.", status_code=201)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        if instance.status not in (Story.Status.DRAFT, Story.Status.REJECTED):
            return error_response(message="Only draft or rejected stories can be edited.")
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return error_response(errors=serializer.errors, message="Update failed.")
        serializer.save()
        return success_response(data=serializer.data, message="Story updated.")

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my(self, request):
        qs = self.get_queryset()
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return success_response(data=self.get_serializer(qs, many=True).data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsOwnerOrAdmin])
    def submit(self, request, pk=None):
        story = self.get_object()
        if story.status != Story.Status.DRAFT:
            return error_response(message="Only draft stories can be submitted.")
        story.status = Story.Status.PENDING
        story.save(update_fields=['status'])
        return success_response(message="Story submitted for review.")

    @action(detail=True, methods=['get'])
    def related(self, request, pk=None):
        story = self.get_object()
        hashtag_ids = story.hashtags.values_list('id', flat=True)
        related = (
            Story.objects
            .filter(status=Story.Status.APPROVED, hashtags__in=hashtag_ids)
            .exclude(pk=story.pk)
            .select_related('user')
            .prefetch_related('hashtags', 'media')
            .distinct()[:10]
        )
        return success_response(data=self.get_serializer(related, many=True).data)

    @action(detail=True, methods=['post'], url_path='media', parser_classes=[MultiPartParser, FormParser])
    def upload_media(self, request, pk=None):
        story = self.get_object()
        serializer = StoryMediaUploadSerializer(data=request.data, context={'story': story})
        if not serializer.is_valid():
            return error_response(errors=serializer.errors, message="Media upload failed.")
        serializer.save()
        return success_response(data=serializer.data, message="Media uploaded.", status_code=201)

    @action(detail=True, methods=['post'], url_path='documents', parser_classes=[MultiPartParser, FormParser])
    def upload_document(self, request, pk=None):
        story = self.get_object()
        serializer = StoryDocumentUploadSerializer(data=request.data, context={'story': story})
        if not serializer.is_valid():
            return error_response(errors=serializer.errors, message="Document upload failed.")
        serializer.save()
        return success_response(data=serializer.data, message="Document uploaded.", status_code=201)


# ── Admin Story ViewSet ───────────────────────────────────────────────────────

class AdminStoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AdminStorySerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        qs = (
            Story.objects
            .select_related('user')
            .prefetch_related('hashtags', 'media', 'documents')
        )
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return success_response(data=self.get_serializer(qs, many=True).data)

    @action(detail=True, methods=['post'], url_path='action')
    def story_action(self, request, pk=None):
        story = self.get_object()
        serializer = StoryActionSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(errors=serializer.errors)

        act = serializer.validated_data['action']
        notes = serializer.validated_data.get('admin_notes', '')

        if story.status != Story.Status.PENDING:
            return error_response(message="Only pending stories can be approved or rejected.")

        story.status = Story.Status.APPROVED if act == 'approve' else Story.Status.REJECTED
        story.admin_notes = notes
        story.save(update_fields=['status', 'admin_notes'])
        return success_response(message=f"Story {story.status}.")


# ── Messaging ViewSet ─────────────────────────────────────────────────────────

class MessageThreadViewSet(viewsets.GenericViewSet):
    """
    3 endpoints:

    GET  /threads/             → list threads (user sees own, admin sees all)
    GET  /threads/{id}/        → full conversation detail + all messages
    POST /threads/             → user sends first message (creates thread if needed)
    POST /threads/{id}/reply/  → admin or user replies in existing thread
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        base = (
            MessageThread.objects
            .select_related('story', 'user', 'admin')
            .prefetch_related('messages__sender')
        )
        if user.is_admin:
            return base.all()
        return base.filter(user=user)

    # 1. List threads
    def list(self, request):
        qs = self.get_queryset()
        page = self.paginate_queryset(qs)
        serializer = MessageThreadListSerializer
        if page is not None:
            return self.get_paginated_response(serializer(page, many=True).data)
        return success_response(data=serializer(qs, many=True).data)

    # 2. Thread detail with all messages
    def retrieve(self, request, pk=None):
        thread = get_object_or_404(self.get_queryset(), pk=pk)
        # mark messages sent to this user as read
        thread.messages.exclude(sender=request.user).filter(is_read=False).update(is_read=True)
        return success_response(data=MessageThreadDetailSerializer(thread).data)

    # 3. User posts a new message (creates thread on first message)
    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['story_id', 'body'],
        properties={
            'story_id': openapi.Schema(type=openapi.TYPE_STRING, format='uuid'),
            'body': openapi.Schema(type=openapi.TYPE_STRING),
        }
    ))
    def create(self, request):
        story_id = request.data.get('story_id')
        body = request.data.get('body', '').strip()

        if not story_id:
            return error_response(message="story_id is required.")
        if not body:
            return error_response(message="body is required.")

        story = get_object_or_404(Story, pk=story_id, status=Story.Status.APPROVED)

        from apps.user_account.models import User
        admin = User.objects.filter(role='admin').first()

        thread, created = get_or_create_thread(story=story, user=request.user, admin=admin)
        Message.objects.create(thread=thread, sender=request.user, body=body)
        thread.save(update_fields=['updated_at'])  # bump updated_at for ordering

        thread.refresh_from_db()
        return success_response(
            data=MessageThreadDetailSerializer(thread).data,
            message="Thread created and message sent." if created else "Message sent.",
            status_code=201 if created else 200,
        )

    # 4. Reply in existing thread (user or admin)
    @swagger_auto_schema(request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['body'],
        properties={
            'body': openapi.Schema(type=openapi.TYPE_STRING),
        }
    ))
    @action(detail=True, methods=['post'])
    def reply(self, request, pk=None):
        thread = get_object_or_404(self.get_queryset(), pk=pk)

        body = request.data.get('body', '').strip()
        if not body:
            return error_response(message="body is required.")

        msg = Message.objects.create(thread=thread, sender=request.user, body=body)
        thread.save(update_fields=['updated_at'])

        return success_response(
            data=MessageSerializer(msg).data,
            message="Reply sent.",
            status_code=201,
        )


# ── Hashtag ViewSet ───────────────────────────────────────────────────────────

class HashtagViewSet(viewsets.ModelViewSet):
    """
    GET    /hashtags/        → list all hashtags (public)
    POST   /hashtags/        → create hashtag (admin only)
    GET    /hashtags/{id}/   → retrieve (public)
    PUT    /hashtags/{id}/   → update (admin only)
    DELETE /hashtags/{id}/   → delete (admin only)
    """
    serializer_class = HashtagSerializer
    queryset = Hashtag.objects.all().order_by('name')

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return [IsAuthenticated(), IsAdminUser()]
