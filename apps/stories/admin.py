from django.contrib import admin
from apps.stories.models import (
    Hashtag, Story, StoryMedia, StoryDocument,
    MessageThread, Message, AdminLog,
)


@admin.register(Hashtag)
class HashtagAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']


class StoryMediaInline(admin.TabularInline):
    model = StoryMedia
    extra = 0
    fields = ['file', 'type']


class StoryDocumentInline(admin.TabularInline):
    model = StoryDocument
    extra = 0
    fields = ['file', 'is_verified']


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'status', 'is_featured', 'view_count', 'total_donated', 'created_at']
    list_filter = ['status', 'is_featured']
    search_fields = ['title', 'content', 'user__email']
    readonly_fields = ['id', 'view_count', 'total_donated', 'created_at', 'updated_at']
    filter_horizontal = ['hashtags']
    list_editable = ['status', 'is_featured']
    inlines = [StoryMediaInline, StoryDocumentInline]
    fieldsets = (
        (None, {'fields': ('id', 'user', 'title', 'content', 'status', 'is_featured')}),
        ('Metadata', {'fields': ('hashtags', 'view_count', 'total_donated', 'admin_notes')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ['sender', 'body', 'is_read', 'created_at']
    can_delete = False


@admin.register(MessageThread)
class MessageThreadAdmin(admin.ModelAdmin):
    list_display = ['id', 'story', 'user', 'admin', 'created_at', 'updated_at']
    search_fields = ['story__title', 'user__email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'thread', 'sender', 'is_read', 'created_at']
    list_filter = ['is_read']
    search_fields = ['body', 'sender__email']
    readonly_fields = ['id', 'created_at']


@admin.register(AdminLog)
class AdminLogAdmin(admin.ModelAdmin):
    list_display = ['admin', 'action', 'target_type', 'target_label', 'created_at']
    list_filter = ['action', 'target_type']
    search_fields = ['admin__email', 'target_label', 'notes']
    readonly_fields = ['id', 'admin', 'action', 'target_type', 'target_id', 'target_label', 'notes', 'created_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
