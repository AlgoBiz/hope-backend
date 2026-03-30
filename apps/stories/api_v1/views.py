from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from apps.stories.models import Story, MessageThread, Message, Hashtag, AdminLog, Testimonial, StoryMedia, StoryDocument, Content
from apps.stories.service import increment_view_count, get_or_create_thread
from apps.stories.api_v1.permissions import IsAdminUser, IsOwnerOrAdmin
from apps.stories.api_v1.serializers import (
    StorySerializer, AdminStorySerializer, StoryActionSerializer,
    StoryMediaUploadSerializer, StoryDocumentUploadSerializer,
    MessageSerializer, MessageThreadDetailSerializer, MessageThreadListSerializer,
    HashtagSerializer, AdminLogSerializer, TestimonialSerializer,
    ContentSerializer,
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
            # support ?hashtag= or ?hashtg= — comma-separated, OR logic
            hashtag = self.request.query_params.get('hashtag') or self.request.query_params.get('hashtg')
            if hashtag:
                tags = [t.strip() for t in hashtag.split(',') if t.strip()]
                qs = qs.filter(hashtags__name__in=tags).distinct()
            featured = self.request.query_params.get('featured')
            if featured is not None:
                qs = qs.filter(is_featured=featured.lower() == 'true')
        elif self.action == 'my':
            qs = qs.filter(user=self.request.user)
        return qs

    def perform_create(self, serializer):
        # kept for DRF compatibility but file handling is done in create()
        serializer.save(user=self.request.user, status=Story.Status.PENDING)

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

    @swagger_auto_schema(
        operation_description="Create a new story. Use multipart/form-data to include files.",
        manual_parameters=[
            openapi.Parameter('title', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('content', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('hashtag_names', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False,
                              description='Comma-separated or repeated field. e.g. health'),
            openapi.Parameter('media_files', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False),
            openapi.Parameter('media_types', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False,
                              description='image or video, one per media_file'),
            openapi.Parameter('document_files', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False),
        ],
        consumes=['multipart/form-data'],
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return error_response(errors=serializer.errors, message="Story creation failed.")
        story = serializer.save(user=request.user, status=Story.Status.PENDING)

        # handle optional file uploads sent alongside story creation
        media_files = request.FILES.getlist('media_files')
        media_types = request.data.getlist('media_types')
        document_files = request.FILES.getlist('document_files')

        for i, file in enumerate(media_files):
            mtype = media_types[i] if i < len(media_types) else 'image'
            StoryMedia.objects.create(story=story, file=file, type=mtype)

        for file in document_files:
            StoryDocument.objects.create(story=story, file=file)

        return success_response(data=self.get_serializer(story).data, message="Story created.", status_code=201)

    @swagger_auto_schema(
        operation_description="Update a story (full). Use multipart/form-data to optionally include and remove files.",
        manual_parameters=[
            openapi.Parameter('title', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('content', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('hashtag_names', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('media_files', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Add new media files"),
            openapi.Parameter('media_types', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Types for new media (image or video)"),
            openapi.Parameter('document_files', openapi.IN_FORM, type=openapi.TYPE_FILE, required=False, description="Add new document files"),
            openapi.Parameter('delete_media_ids', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Comma-separated IDs of media to remove"),
            openapi.Parameter('delete_document_ids', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False, description="Comma-separated IDs of docs to remove"),
        ],
        consumes=['multipart/form-data'],
    )
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        if instance.status not in (Story.Status.DRAFT, Story.Status.PENDING, Story.Status.REJECTED):
            return error_response(message="Only draft, pending, or rejected stories can be edited.")
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return error_response(errors=serializer.errors, message="Update failed.")
        
        story = serializer.save()

        # Add new files
        media_files = request.FILES.getlist('media_files')
        media_types = request.data.getlist('media_types')
        document_files = request.FILES.getlist('document_files')

        for i, file in enumerate(media_files):
            mtype = media_types[i] if i < len(media_types) else 'image'
            StoryMedia.objects.create(story=story, file=file, type=mtype)

        for file in document_files:
            StoryDocument.objects.create(story=story, file=file)

        # Delete requested files
        delete_media_ids = request.data.getlist('delete_media_ids')
        if delete_media_ids:
            ids = [i.strip() for item in delete_media_ids for i in item.split(',') if i.strip()]
            if ids:
                StoryMedia.objects.filter(story=story, id__in=ids).delete()

        delete_doc_ids = request.data.getlist('delete_document_ids')
        if delete_doc_ids:
            ids = [i.strip() for item in delete_doc_ids for i in item.split(',') if i.strip()]
            if ids:
                StoryDocument.objects.filter(story=story, id__in=ids).delete()

        return success_response(data=self.get_serializer(story).data, message="Story updated.")

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my(self, request):
        qs = self.get_queryset()
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return success_response(data=self.get_serializer(qs, many=True).data)

    @action(detail=False, methods=['get'], url_path='unread-messages', permission_classes=[IsAuthenticated])
    def unread_messages(self, request):
        from django.db.models import Count, Q
        qs = Story.objects.filter(user=request.user).annotate(
            new_message_count=Count(
                'threads__messages',
                filter=Q(threads__messages__is_read=False) & ~Q(threads__messages__sender=request.user)
            )
        )
        
        data = qs.values('id', 'title', 'new_message_count').order_by('-updated_at')
        return success_response(data=list(data))

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsOwnerOrAdmin])
    def submit(self, request, pk=None):
        story = self.get_object()
        if story.status != Story.Status.DRAFT:
            return error_response(message="Only draft stories can be submitted.")
        story.status = Story.Status.PENDING
        story.save(update_fields=['status'])
        return success_response(message="Story submitted for review.")

    @action(detail=True, methods=['post'], url_path='view', permission_classes=[AllowAny])
    def track_view(self, request, pk=None):
        story = get_object_or_404(Story, pk=pk, status=Story.Status.APPROVED)
        increment_view_count(story)
        return success_response(message="View counted.")

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

    @action(detail=True, methods=['get', 'post'], url_path='messages', permission_classes=[IsAuthenticated])
    def messages(self, request, pk=None):
        story = get_object_or_404(Story, pk=pk)
        
        # Security: Only story owner and admins can access messages
        if not request.user.is_admin and story.user != request.user:
            return error_response(message="Permission denied to access this story's messages.", status_code=403)
            
        from apps.user_account.models import User
        admin = User.objects.filter(role='admin').first()
        thread, created = get_or_create_thread(story=story, user=story.user, admin=admin)

        if request.method == 'GET':
            # Mark messages received by this user as read
            thread.messages.exclude(sender=request.user).filter(is_read=False).update(is_read=True)
            return success_response(data=MessageThreadDetailSerializer(thread).data)

        elif request.method == 'POST':
            if not request.user.is_admin and not thread.is_reply:
                return error_response(message="Admin must enable replies before you can respond.", status_code=403)

            body = request.data.get('body', '').strip()
            if not body:
                return error_response(message="body is required.", status_code=400)
            
            # Allow admins to dynamically toggle the is_reply lock while sending a message
            if request.user.is_admin and 'is_reply' in request.data:
                thread.is_reply = str(request.data['is_reply']).lower() == 'true'

            msg = Message.objects.create(thread=thread, sender=request.user, body=body)
            thread.save(update_fields=['updated_at', 'is_reply'])

            if request.user.is_admin:
                AdminLog.objects.create(
                    admin=request.user,
                    action=AdminLog.Action.MESSAGE_SENT,
                    target_type='MessageThread',
                    target_id=str(thread.id),
                    target_label=story.title,
                    notes=body[:200],
                )

            return success_response(
                data=MessageSerializer(msg).data,
                message="Reply sent." if not created else "Message sent and thread created.",
                status_code=201
            )

    @action(detail=True, methods=['post'], url_path='media', parser_classes=[MultiPartParser, FormParser])
    @swagger_auto_schema(
        operation_description="Upload image or video to a story. Use multipart/form-data.",
        manual_parameters=[
            openapi.Parameter('file', openapi.IN_FORM, type=openapi.TYPE_FILE, required=True),
            openapi.Parameter('type', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, enum=['image', 'video']),
        ]
    )
    def upload_media(self, request, pk=None):
        story = self.get_object()
        serializer = StoryMediaUploadSerializer(data=request.data, context={'story': story})
        if not serializer.is_valid():
            return error_response(errors=serializer.errors, message="Media upload failed.")
        serializer.save()
        return success_response(data=serializer.data, message="Media uploaded.", status_code=201)

    @action(detail=True, methods=['post'], url_path='documents', parser_classes=[MultiPartParser, FormParser])
    @swagger_auto_schema(
        operation_description="Upload a supporting document to a story. Use multipart/form-data.",
        manual_parameters=[
            openapi.Parameter('file', openapi.IN_FORM, type=openapi.TYPE_FILE, required=True),
        ]
    )
    def upload_document(self, request, pk=None):
        story = self.get_object()
        serializer = StoryDocumentUploadSerializer(data=request.data, context={'story': story})
        if not serializer.is_valid():
            return error_response(errors=serializer.errors, message="Document upload failed.")
        serializer.save()
        return success_response(data=serializer.data, message="Document uploaded.", status_code=201)

    @action(detail=True, methods=['delete'], url_path='media/(?P<media_id>[^/.]+)', permission_classes=[IsAuthenticated, IsOwnerOrAdmin])
    def delete_media(self, request, pk=None, media_id=None):
        story = self.get_object()
        media = get_object_or_404(StoryMedia, pk=media_id, story=story)
        media.delete()
        return success_response(message="Media deleted.")

    @action(detail=True, methods=['delete'], url_path='documents/(?P<doc_id>[^/.]+)', permission_classes=[IsAuthenticated, IsOwnerOrAdmin])
    def delete_document(self, request, pk=None, doc_id=None):
        story = self.get_object()
        doc = get_object_or_404(StoryDocument, pk=doc_id, story=story)
        doc.delete()
        return success_response(message="Document deleted.")


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

        if story.status not in (Story.Status.PENDING, Story.Status.REJECTED):
            return error_response(message="Only pending or rejected stories can be approved or rejected.")

        story.status = Story.Status.APPROVED if act == 'approve' else Story.Status.REJECTED
        story.admin_notes = notes
        story.save(update_fields=['status', 'admin_notes'])

        AdminLog.objects.create(
            admin=request.user,
            action=AdminLog.Action.STORY_APPROVED if act == 'approve' else AdminLog.Action.STORY_REJECTED,
            target_type='Story',
            target_id=str(story.id),
            target_label=story.title,
            notes=notes,
        )
        return success_response(message=f"Story {story.status}.")

    @action(detail=True, methods=['post'], url_path='feature')
    def feature(self, request, pk=None):
        story = self.get_object()
        story.is_featured = not story.is_featured
        story.save(update_fields=['is_featured'])
        AdminLog.objects.create(
            admin=request.user,
            action=AdminLog.Action.OTHER,
            target_type='Story',
            target_id=str(story.id),
            target_label=story.title,
            notes=f"Story {'featured' if story.is_featured else 'unfeatured'}.",
        )
        return success_response(
            data={'is_featured': story.is_featured},
            message=f"Story {'featured' if story.is_featured else 'unfeatured'}.",
        )

    @action(detail=True, methods=['post'], url_path='toggle-reply')
    def toggle_reply(self, request, pk=None):
        story = self.get_object()
        
        from apps.user_account.models import User
        admin = User.objects.filter(role='admin').first()
        thread, created = get_or_create_thread(story=story, user=story.user, admin=admin)

        target_state = request.data.get('is_reply')
        if target_state is not None:
            thread.is_reply = str(target_state).lower() in ['true', '1', 'yes']
        else:
            thread.is_reply = not thread.is_reply
            
        thread.save(update_fields=['is_reply'])
        return success_response(
            data={"is_reply": thread.is_reply},
            message=f"User replies {'enabled' if thread.is_reply else 'disabled'}."
        )


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

        if request.user.is_admin:
            AdminLog.objects.create(
                admin=request.user,
                action=AdminLog.Action.MESSAGE_SENT,
                target_type='MessageThread',
                target_id=str(thread.id),
                target_label=thread.story.title,
                notes=body[:200],
            )

        return success_response(
            data=MessageSerializer(msg).data,
            message="Reply sent.",
            status_code=201,
        )


# ── Hashtag ViewSet ───────────────────────────────────────────────────────────

class HashtagViewSet(viewsets.ModelViewSet):
    serializer_class = HashtagSerializer
    queryset = Hashtag.objects.all().order_by('name')
    pagination_class = None

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return [IsAuthenticated(), IsAdminUser()]

    def list(self, request):
        return success_response(data=self.get_serializer(self.get_queryset(), many=True).data)


# ── Admin Log ViewSet ─────────────────────────────────────────────────────────

class AdminLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /admin/logs/        → paginated list of all admin actions
    GET /admin/logs/{id}/   → single log entry
    """
    serializer_class = AdminLogSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        qs = AdminLog.objects.select_related('admin')
        action_filter = self.request.query_params.get('action')
        if action_filter:
            qs = qs.filter(action=action_filter)
        return qs

    def list(self, request):
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(AdminLogSerializer(page, many=True).data)
        return success_response(data=AdminLogSerializer(qs, many=True).data)

    def retrieve(self, request, pk=None):
        log = get_object_or_404(self.get_queryset(), pk=pk)
        return success_response(data=AdminLogSerializer(log).data)


# ── Admin Dashboard ───────────────────────────────────────────────────────────

class AdminDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    @swagger_auto_schema(responses={200: 'Dashboard stats'})
    def get(self, request):
        from django.utils import timezone
        from django.db.models import Sum
        from apps.user_account.models import User

        now = timezone.now()
        # current month window
        this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # previous month window
        prev_month_end = this_month_start
        prev_month_start = (this_month_start.replace(day=1) - timezone.timedelta(days=1)).replace(day=1)

        def pct_change(current, previous):
            if previous == 0:
                return 100.0 if current > 0 else 0.0
            return round((current - previous) / previous * 100, 1)

        # ── Users (non-admin) ─────────────────────────────────────────────────
        total_users = User.objects.filter(role='user').count()
        users_this  = User.objects.filter(role='user', created_at__gte=this_month_start).count()
        users_prev  = User.objects.filter(role='user', created_at__gte=prev_month_start, created_at__lt=prev_month_end).count()

        # ── Stories submitted (pending + approved + rejected) ─────────────────
        total_stories = Story.objects.exclude(status=Story.Status.DRAFT).count()
        stories_this  = Story.objects.exclude(status=Story.Status.DRAFT).filter(created_at__gte=this_month_start).count()
        stories_prev  = Story.objects.exclude(status=Story.Status.DRAFT).filter(created_at__gte=prev_month_start, created_at__lt=prev_month_end).count()

        # ── Total views ───────────────────────────────────────────────────────
        total_views = Story.objects.aggregate(t=Sum('view_count'))['t'] or 0
        # views growth: compare approved stories created this vs prev month as proxy
        views_this = Story.objects.filter(created_at__gte=this_month_start).aggregate(t=Sum('view_count'))['t'] or 0
        views_prev = Story.objects.filter(created_at__gte=prev_month_start, created_at__lt=prev_month_end).aggregate(t=Sum('view_count'))['t'] or 0

        # ── Payments received ─────────────────────────────────────────────────
        payment_total = 0
        payment_this  = 0
        payment_prev  = 0
        try:
            from apps.payments.models import Donation
            payment_total = Donation.objects.aggregate(t=Sum('amount'))['t'] or 0
            payment_this  = Donation.objects.filter(created_at__gte=this_month_start).aggregate(t=Sum('amount'))['t'] or 0
            payment_prev  = Donation.objects.filter(created_at__gte=prev_month_start, created_at__lt=prev_month_end).aggregate(t=Sum('amount'))['t'] or 0
        except Exception:
            pass

        # ── Top 5 most viewed stories ─────────────────────────────────────────
        top_stories = (
            Story.objects.filter(status=Story.Status.APPROVED)
            .order_by('-view_count')[:5]
            .values('id', 'title', 'view_count', 'created_at')
        )

        # ── Recent 5 stories (latest submitted) ───────────────────────────────
        recent_stories = (
            Story.objects.exclude(status=Story.Status.DRAFT)
            .order_by('-created_at')[:5]
            .values('id', 'title', 'status', 'created_at')
        )

        # ── Last 5 admin activity logs ────────────────────────────────────────
        recent_activity = AdminLogSerializer(
            AdminLog.objects.select_related('admin').order_by('-created_at')[:5],
            many=True
        ).data

        return success_response(data={
            "stats": {
                "total_users":   {"count": total_users,       "change_pct": pct_change(users_this, users_prev)},
                "stories_submitted": {"count": total_stories, "change_pct": pct_change(stories_this, stories_prev)},
                "total_views":   {"count": total_views,       "change_pct": pct_change(views_this, views_prev)},
                "payment_received": {"amount": float(payment_total), "change_pct": pct_change(float(payment_this), float(payment_prev))},
            },
            "top_stories":     list(top_stories),
            "recent_stories":  list(recent_stories),
            "recent_activity": recent_activity,
        })


# ── Reports & Analytics ───────────────────────────────────────────────────────

class AnalyticsReportView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    @swagger_auto_schema(responses={200: 'Analytics payload matching UI'})
    def get(self, request):
        from django.utils import timezone
        from django.db.models import Sum
        from apps.user_account.models import User
        from apps.stories.models import Story

        now = timezone.now()
        this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # 1. Story Posting Report
        stories_all = Story.objects.exclude(status=Story.Status.DRAFT)
        total_submitted = stories_all.count()
        approved = stories_all.filter(status=Story.Status.APPROVED).count()
        pending = stories_all.filter(status=Story.Status.PENDING).count()
        rejected = stories_all.filter(status=Story.Status.REJECTED).count()
        this_month_stories = stories_all.filter(created_at__gte=this_month_start).count()

        story_posting_report = {
            "total_submitted": total_submitted,
            "approved": approved,
            "pending_review": pending,
            "rejected": rejected,
            "this_month": this_month_stories,
        }

        # 2. Payment Report
        total_revenue = 0
        completed_payments = 0
        pending_payments = 0
        this_month_revenue = 0
        avg_per_month = 0
        try:
            from apps.payments.models import Donation
            donations = Donation.objects.all()
            total_revenue = donations.aggregate(t=Sum('amount'))['t'] or 0
            completed_payments = donations.count()
            this_month_revenue = donations.filter(created_at__gte=this_month_start).aggregate(t=Sum('amount'))['t'] or 0
            first_txn = donations.order_by('created_at').first()
            if first_txn:
                months = (now.year - first_txn.created_at.year) * 12 + now.month - first_txn.created_at.month + 1
                avg_per_month = total_revenue / months if months > 0 else total_revenue
        except Exception:
            pass

        payment_report = {
            "total_revenue": float(total_revenue),
            "completed_payments": completed_payments,
            "pending": pending_payments,
            "this_month_revenue": float(this_month_revenue),
            "average_per_month": float(avg_per_month)
        }

        # 3. Reader Analytics
        appr_stories = Story.objects.filter(status=Story.Status.APPROVED)
        total_page_views = appr_stories.aggregate(t=Sum('view_count'))['t'] or 0
        unique_readers = User.objects.filter(role='user').count()
        total_ap_stories = appr_stories.count()
        avg_views = total_page_views / total_ap_stories if total_ap_stories else 0
        most_read = appr_stories.order_by('-view_count').first()
        most_read_views = most_read.view_count if most_read else 0
        this_month_views = appr_stories.filter(created_at__gte=this_month_start).aggregate(t=Sum('view_count'))['t'] or 0

        reader_analytics = {
            "total_page_views": total_page_views,
            "unique_readers": unique_readers,
            "avg_views_per_story": int(avg_views),
            "most_read_story_views": most_read_views,
            "this_month_views": this_month_views,
        }

        # 4. Monthly Trends (Submissions over last 12 months)
        import calendar
        monthly_trends = []
        for i in range(11, -1, -1):
            t_month = (now.month - i - 1) % 12 + 1
            t_year = now.year - 1 if (now.month - i - 1) < 0 else now.year
            m_s = now.replace(year=t_year, month=t_month, day=1, hour=0, minute=0, second=0, microsecond=0)
            if t_month == 12:
                m_e = m_s.replace(year=t_year + 1, month=1)
            else:
                m_e = m_s.replace(month=t_month + 1)
            
            # Plot completed payments as proxy for trend if desired, or story submissions? Let's do story submissions.
            v = Story.objects.exclude(status=Story.Status.DRAFT).filter(created_at__gte=m_s, created_at__lt=m_e).count()
            monthly_trends.append({
                "month": calendar.month_abbr[t_month][0], # 'J', 'F', 'M'
                "value": v
            })

        return success_response(data={
            "story_posting_report": story_posting_report,
            "payment_report": payment_report,
            "reader_analytics": reader_analytics,
            "monthly_trends": monthly_trends
        })


# ── Testimonial ViewSet ───────────────────────────────────────────────────────

class TestimonialViewSet(viewsets.ModelViewSet):
    """
    GET    /testimonials/       → public list (active only, no pagination)
    POST   /testimonials/       → admin create
    PUT    /testimonials/{id}/  → admin update
    DELETE /testimonials/{id}/  → admin delete
    """
    serializer_class = TestimonialSerializer
    pagination_class = None
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        if self.action == 'list':
            return Testimonial.objects.filter(is_active=True)
        return Testimonial.objects.all()

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return [IsAuthenticated(), IsAdminUser()]

    def list(self, request):
        return success_response(data=self.get_serializer(self.get_queryset(), many=True).data)


# ── Content ViewSet ───────────────────────────────────────────────────────────

class ContentViewSet(viewsets.ModelViewSet):
    """
    GET    /content/       → public list
    GET    /content/{id}/  → public retrieve
    POST   /content/       → admin create
    PUT    /content/{id}/  → admin update
    DELETE /content/{id}/  → admin delete
    """
    serializer_class = ContentSerializer
    queryset = Content.objects.all()

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return [IsAuthenticated(), IsAdminUser()]

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(self.get_serializer(page, many=True).data)
        return success_response(data=self.get_serializer(qs, many=True).data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return success_response(data=self.get_serializer(instance).data)
