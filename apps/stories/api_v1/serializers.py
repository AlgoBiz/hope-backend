from rest_framework import serializers
from apps.stories.models import (
    Story, StoryMedia, StoryDocument, Hashtag,
    MessageThread, Message, AdminLog,
)


# ── Hashtag ──────────────────────────────────────────────────────────────────

class HashtagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hashtag
        fields = ['id', 'name']


# ── Media / Document ──────────────────────────────────────────────────────────

class StoryMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoryMedia
        fields = ['id', 'file', 'type']


class StoryDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoryDocument
        fields = ['id', 'file', 'is_verified']


# ── Story (user-facing) ───────────────────────────────────────────────────────

class StorySerializer(serializers.ModelSerializer):
    hashtags = HashtagSerializer(many=True, read_only=True)
    hashtag_names = serializers.ListField(
        child=serializers.CharField(max_length=100),
        write_only=True, required=False, default=list,
    )
    media = StoryMediaSerializer(many=True, read_only=True)
    documents = StoryDocumentSerializer(many=True, read_only=True)
    author_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Story
        fields = [
            'id', 'author_email', 'title', 'content', 'status',
            'hashtags', 'hashtag_names', 'media', 'documents',
            'view_count', 'total_donated', 'is_featured', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'status', 'view_count', 'total_donated', 'is_featured', 'created_at', 'updated_at']

    def create(self, validated_data):
        from apps.stories.service import get_or_create_hashtags
        hashtag_names = validated_data.pop('hashtag_names', [])
        story = Story.objects.create(**validated_data)
        if hashtag_names:
            story.hashtags.set(get_or_create_hashtags(hashtag_names))
        return story

    def update(self, instance, validated_data):
        from apps.stories.service import get_or_create_hashtags
        hashtag_names = validated_data.pop('hashtag_names', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if hashtag_names is not None:
            instance.hashtags.set(get_or_create_hashtags(hashtag_names))
        return instance


# ── Story (admin-facing) ──────────────────────────────────────────────────────

class AdminStorySerializer(StorySerializer):
    class Meta(StorySerializer.Meta):
        fields = StorySerializer.Meta.fields + ['admin_notes']
        read_only_fields = ['id', 'view_count', 'total_donated', 'created_at', 'updated_at']


class StoryActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    admin_notes = serializers.CharField(required=False, allow_blank=True)


# ── Media upload ──────────────────────────────────────────────────────────────

class StoryMediaUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoryMedia
        fields = ['id', 'file', 'type']

    def create(self, validated_data):
        story = self.context['story']
        return StoryMedia.objects.create(story=story, **validated_data)


class StoryDocumentUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoryDocument
        fields = ['id', 'file']

    def create(self, validated_data):
        story = self.context['story']
        return StoryDocument.objects.create(story=story, **validated_data)


# ── Messaging ─────────────────────────────────────────────────────────────────

class MessageSerializer(serializers.ModelSerializer):
    sender_email = serializers.EmailField(source='sender.email', read_only=True)
    sender_role = serializers.CharField(source='sender.role', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'sender_email', 'sender_role', 'body', 'is_read', 'created_at']
        read_only_fields = ['id', 'sender_email', 'sender_role', 'is_read', 'created_at']


class MessageThreadDetailSerializer(serializers.ModelSerializer):
    """Full conversation with all messages — used in detail view."""
    messages = MessageSerializer(many=True, read_only=True)
    story_id = serializers.UUIDField(source='story.id', read_only=True)
    story_title = serializers.CharField(source='story.title', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = MessageThread
        fields = ['id', 'story_id', 'story_title', 'user_email', 'message_count', 'messages', 'created_at', 'updated_at']
        read_only_fields = fields

    def get_message_count(self, obj):
        return obj.messages.count()


class MessageThreadListSerializer(serializers.ModelSerializer):
    """Lightweight — for thread list (left sidebar)."""
    story_id = serializers.UUIDField(source='story.id', read_only=True)
    story_title = serializers.CharField(source='story.title', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    last_message = serializers.SerializerMethodField()
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = MessageThread
        fields = ['id', 'story_id', 'story_title', 'user_email', 'message_count', 'last_message', 'created_at', 'updated_at']
        read_only_fields = fields

    def get_last_message(self, obj):
        msg = obj.messages.order_by('-created_at').first()
        if msg:
            return {'body': msg.body, 'sender_email': msg.sender.email, 'created_at': msg.created_at}
        return None

    def get_message_count(self, obj):
        return obj.messages.count()


# keep old name as alias so existing imports don't break
MessageThreadSerializer = MessageThreadDetailSerializer


# ── Admin Log ─────────────────────────────────────────────────────────────────

class AdminLogSerializer(serializers.ModelSerializer):
    admin_email = serializers.EmailField(source='admin.email', read_only=True)

    class Meta:
        model = AdminLog
        fields = [
            'id', 'admin_email', 'action', 'target_type',
            'target_id', 'target_label', 'notes', 'created_at',
        ]
        read_only_fields = fields
