from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from apps.user_account.models import User, Profile, OTPVerification


class ProfileInline(admin.StackedInline):
    model = Profile
    extra = 0
    fields = ['full_name', 'business_name', 'country', 'bio', 'avatar_url', 'can_reply']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'role', 'is_active', 'is_verified', 'is_staff', 'created_at']
    list_filter = ['role', 'is_active', 'is_verified', 'is_staff']
    search_fields = ['email']
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_login']
    list_editable = ['is_active', 'is_verified']
    inlines = [ProfileInline]

    fieldsets = (
        (None, {'fields': ('id', 'email', 'password')}),
        ('Role & Status', {'fields': ('role', 'is_active', 'is_verified', 'is_staff', 'is_superuser')}),
        ('Timestamps', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role', 'is_active', 'is_verified', 'is_staff'),
        }),
    )

    filter_horizontal = ['groups', 'user_permissions']


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'business_name', 'country', 'can_reply', 'created_at']
    search_fields = ['user__email', 'full_name', 'business_name']
    list_filter = ['country', 'can_reply']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'purpose', 'is_used', 'expires_at', 'created_at']
    list_filter = ['purpose', 'is_used']
    search_fields = ['user__email']
    readonly_fields = ['id', 'user', 'code', 'purpose', 'is_used', 'expires_at', 'created_at']

    def has_add_permission(self, request):
        return False
