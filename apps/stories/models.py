import uuid
from django.db import models
from django.conf import settings


class Hashtag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Story(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='stories')
    title = models.CharField(max_length=255)
    content = models.TextField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    hashtags = models.ManyToManyField(Hashtag, blank=True, related_name='stories')
    view_count = models.PositiveIntegerField(default=0)
    total_donated = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_featured = models.BooleanField(default=False)
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'stories'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return self.title


class StoryMedia(models.Model):
    class MediaType(models.TextChoices):
        IMAGE = 'image', 'Image'
        VIDEO = 'video', 'Video'

    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='media')
    file = models.FileField(upload_to='stories/media/')
    type = models.CharField(max_length=10, choices=MediaType.choices)

    class Meta:
        db_table = 'story_media'


class StoryDocument(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to='stories/documents/')
    is_verified = models.BooleanField(default=False)

    class Meta:
        db_table = 'story_documents'



class MessageThread(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='threads')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_threads')
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='admin_threads'
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'message_threads'
        unique_together = ('story', 'user')
        ordering = ['-updated_at']


class Message(models.Model):
    thread = models.ForeignKey(MessageThread, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'messages'
        ordering = ['created_at']


class AdminLog(models.Model):
    class Action(models.TextChoices):
        STORY_APPROVED  = 'story_approved',  'Story Approved'
        STORY_REJECTED  = 'story_rejected',  'Story Rejected'
        STORY_DELETED   = 'story_deleted',   'Story Deleted'
        MESSAGE_SENT    = 'message_sent',    'Message Sent'
        USER_ACTIVATED  = 'user_activated',  'User Activated'
        USER_DEACTIVATED = 'user_deactivated', 'User Deactivated'
        OTHER           = 'other',           'Other'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='admin_logs'
    )
    action = models.CharField(max_length=30, choices=Action.choices)
    target_type = models.CharField(max_length=50, blank=True)   # e.g. "Story", "User"
    target_id = models.CharField(max_length=100, blank=True)    # pk of the target object
    target_label = models.CharField(max_length=255, blank=True) # human-readable name
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'admin_logs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.admin} → {self.action} [{self.target_label}]"


class Testimonial(models.Model):
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100, blank=True)  # e.g. "Robust bakery business"
    quote = models.TextField()
    avatar_url = models.ImageField(upload_to='testimonials/avatars/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'testimonials'
        ordering = ['order', '-created_at']

    def __str__(self):
        return f"{self.name} — {self.role}"



class Content(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'content'
        ordering = ['-created_at']

    def __str__(self):
        return self.title