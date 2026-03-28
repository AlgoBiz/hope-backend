from django.urls import path
from apps.user_account.api_v1.views import (
    RegisterView,
    VerifyEmailView,
    LoginView,
    TokenRefreshView,
    LogoutView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    ChangePasswordView,
    MeView,
    ProfileUpdateView,
    AdminUserListView,
    AdminUserDetailView,
)

app_name = "user_account_api_router_v1"

urlpatterns = [
    # Auth
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    # Password
    path("auth/password-reset/", PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("auth/password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("auth/change-password/", ChangePasswordView.as_view(), name="change-password"),
    # User
    path("auth/me/", MeView.as_view(), name="me"),
    path("profile/", ProfileUpdateView.as_view(), name="profile"),
    # Admin — Users
    path("admin/users/", AdminUserListView.as_view(), name="admin-user-list"),
    path("admin/users/<uuid:user_id>/", AdminUserDetailView.as_view(), name="admin-user-detail"),
]
