from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from apps.user_account.api_v1.serializers import (
    RegisterSerializer,
    VerifyEmailSerializer,
    LoginSerializer,
    TokenRefreshSerializer,
    LogoutSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    ChangePasswordSerializer,
    ProfileSerializer,
    UserMeSerializer,
)
from apps.user_account.models import Profile
from apps.user_account.service import create_otp
from apps.user_account.email_service import send_otp_email
from apps.user_account.utils import success_response, error_response


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(errors=serializer.errors, message="Registration failed.")
        user = serializer.save()
        Profile.objects.get_or_create(user=user)
        return success_response(
            data={"email": user.email},
            message="Registration successful. Check your email for the OTP.",
            status_code=201,
        )


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(errors=serializer.errors, message="Verification failed.")
        user = serializer.validated_data['user']
        user.is_verified = True
        user.save(update_fields=['is_verified'])
        return success_response(message="Email verified successfully.")


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(errors=serializer.errors, message="Login failed.")
        data = serializer.validated_data
        return success_response(data={
            "access": data['access'],
            "refresh": data['refresh'],
            "role": data['user'].role,
        }, message="Login successful.")


class TokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(errors=serializer.errors, message="Token refresh failed.")
        return success_response(data=serializer.validated_data, message="Token refreshed.")


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(errors=serializer.errors, message="Logout failed.")
        return success_response(message="Logged out successfully.")


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return error_response(errors=serializer.errors, message="Request failed.")
        user = serializer.context['user']
        otp = create_otp(user, 'password_reset')
        send_otp_email(user.email, otp.code)
        return success_response(message="OTP sent to your email.")


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(errors=serializer.errors, message="Password reset failed.")
        user = serializer.validated_data['user']
        user.set_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password'])
        return success_response(message="Password reset successful.")


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return error_response(errors=serializer.errors, message="Password change failed.")
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save(update_fields=['password'])
        return success_response(message="Password changed successfully.")


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserMeSerializer(request.user)
        return success_response(data=serializer.data)


class ProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile)
        return success_response(data=serializer.data)

    def patch(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(errors=serializer.errors, message="Profile update failed.")
        serializer.save()
        return success_response(data=serializer.data, message="Profile updated.")
