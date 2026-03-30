from django.contrib import admin
from apps.stories.models import (
    Hashtag, Story, StoryMedia, StoryDocument,
    MessageThread, Message, AdminLog, Testimonial,
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


from django import forms
from apps.stories.service import get_or_create_thread

class StoryAdminForm(forms.ModelForm):
    new_message = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        help_text="Type here to instantly send a message to the author's story thread.",
        label="Send Message to Author"
    )

    class Meta:
        model = Story
        fields = '__all__'


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    form = StoryAdminForm
    list_display = ['title', 'user', 'status', 'is_featured', 'view_count', 'total_donated', 'created_at']
    list_filter = ['status', 'is_featured']
    search_fields = ['title', 'content', 'user__email']
    readonly_fields = ['id', 'view_count', 'total_donated', 'created_at', 'updated_at']
    filter_horizontal = ['hashtags']
    list_editable = ['status', 'is_featured']
    inlines = [StoryMediaInline, StoryDocumentInline]
    fieldsets = (
        (None, {'fields': ('id', 'user', 'title', 'content', 'status', 'is_featured')}),
        ('Messaging', {'fields': ('new_message',)}),
        ('Metadata', {'fields': ('hashtags', 'view_count', 'total_donated', 'admin_notes')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        msg_text = form.cleaned_data.get('new_message')
        if msg_text:
            thread, created = get_or_create_thread(story=obj, user=obj.user, admin=request.user)
            Message.objects.create(thread=thread, sender=request.user, body=msg_text)
            thread.save(update_fields=['updated_at'])
            
            AdminLog.objects.create(
                admin=request.user,
                action=AdminLog.Action.MESSAGE_SENT,
                target_type='MessageThread',
                target_id=str(thread.id),
                target_label=obj.title,
                notes=msg_text[:200],
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


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['name', 'role', 'is_active', 'order', 'created_at']
    list_editable = ['is_active', 'order']
    search_fields = ['name', 'role', 'quote']
    list_filter = ['is_active']


from apps.stories.models import ContactForm

@admin.register(ContactForm)
class ContactFormAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'subject', 'created_at']
    search_fields = ['full_name', 'email', 'subject', 'message']
    readonly_fields = ['created_at']
