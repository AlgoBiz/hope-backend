from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
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
    AdminUserListSerializer,
)
from apps.user_account.models import User, Profile
from apps.user_account.service import create_otp
from apps.user_account.email_service import send_otp_email
from apps.user_account.utils import success_response, error_response


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=RegisterSerializer)
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(errors=serializer.errors, message="Registration failed.")
        user = serializer.save()
        return success_response(
            data={
                "email": user.email,
                "full_name": user.profile.full_name,
            },
            message="Registration successful. Check your email for the OTP.",
            status_code=201,
        )


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=VerifyEmailSerializer)
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

    @swagger_auto_schema(request_body=LoginSerializer)
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

    @swagger_auto_schema(request_body=TokenRefreshSerializer)
    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(errors=serializer.errors, message="Token refresh failed.")
        return success_response(data=serializer.validated_data, message="Token refreshed.")


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=LogoutSerializer)
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(errors=serializer.errors, message="Logout failed.")
        return success_response(message="Logged out successfully.")


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=PasswordResetRequestSerializer)
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return error_response(errors=serializer.errors, message="Request failed.")
        user = serializer.context['user']
        otp = create_otp(user, 'password_reset')
        send_otp_email(user.email, otp.code, purpose='password_reset')
        return success_response(message="OTP sent to your email.")


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(request_body=PasswordResetConfirmSerializer)
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

    @swagger_auto_schema(request_body=ChangePasswordSerializer)
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return error_response(errors=serializer.errors, message="Password change failed.")
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save(update_fields=['password'])
        return success_response(message="Password changed successfully.")


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(responses={200: UserMeSerializer})
    def get(self, request):
        serializer = UserMeSerializer(request.user)
        return success_response(data=serializer.data)


class ProfileUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(responses={200: ProfileSerializer})
    def get(self, request):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile)
        return success_response(data=serializer.data)

    def _update_profile(self, request, partial=False):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        
        allowed_data = {}
        if 'full_name' in request.data:
            allowed_data['full_name'] = request.data['full_name']
        
        # Accommodate 'business' or 'business_name' keys from frontend
        if 'business_name' in request.data:
            allowed_data['business_name'] = request.data['business_name']
        elif 'business' in request.data:
            allowed_data['business_name'] = request.data['business']

        serializer = ProfileSerializer(profile, data=allowed_data, partial=partial)
        if not serializer.is_valid():
            return error_response(errors=serializer.errors, message="Profile update failed.")
        serializer.save()
        return success_response(data=serializer.data, message="Profile updated.")

    @swagger_auto_schema(request_body=ProfileSerializer)
    def put(self, request):
        return self._update_profile(request, partial=False)

    @swagger_auto_schema(request_body=ProfileSerializer)
    def patch(self, request):
        return self._update_profile(request, partial=True)


class AdminUserListView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Admin only. List all non-admin users with their profile data.",
        manual_parameters=[
            openapi.Parameter('is_active', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN,
                              required=False, description='Filter by active status'),
            openapi.Parameter('is_verified', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN,
                              required=False, description='Filter by email verification status'),
            openapi.Parameter('search', openapi.IN_QUERY, type=openapi.TYPE_STRING,
                              required=False, description='Search by email or full name'),
            openapi.Parameter('page', openapi.IN_QUERY, type=openapi.TYPE_INTEGER,
                              required=False),
        ],
        responses={200: AdminUserListSerializer(many=True)},
    )
    def get(self, request):
        if not request.user.is_admin:
            return error_response(message="Permission denied.", status_code=403)

        qs = (
            User.objects
            .filter(role=User.Role.USER)
            .select_related('profile')
            .order_by('-created_at')
        )

        is_active = request.query_params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == 'true')

        is_verified = request.query_params.get('is_verified')
        if is_verified is not None:
            qs = qs.filter(is_verified=is_verified.lower() == 'true')

        search = request.query_params.get('search')
        if search:
            qs = qs.filter(email__icontains=search) | qs.filter(profile__full_name__icontains=search)

        # pagination
        from rest_framework.pagination import PageNumberPagination
        paginator = PageNumberPagination()
        paginator.page_size = 10
        page = paginator.paginate_queryset(qs, request)
        if page is not None:
            serializer = AdminUserListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = AdminUserListSerializer(qs, many=True)
        return success_response(data=serializer.data)


class AdminUserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Admin only. Get a single user with profile data.",
        responses={200: AdminUserListSerializer},
    )
    def get(self, request, user_id):
        if not request.user.is_admin:
            return error_response(message="Permission denied.", status_code=403)
        try:
            user = User.objects.select_related('profile').get(id=user_id, role=User.Role.USER)
        except User.DoesNotExist:
            return error_response(message="User not found.", status_code=404)
        return success_response(data=AdminUserListSerializer(user).data)

    @swagger_auto_schema(
        operation_description="Admin only. Toggle active/inactive status of a user.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN),
            },
            required=['is_active'],
        ),
    )
    def patch(self, request, user_id):
        if not request.user.is_admin:
            return error_response(message="Permission denied.", status_code=403)
        try:
            user = User.objects.get(id=user_id, role=User.Role.USER)
        except User.DoesNotExist:
            return error_response(message="User not found.", status_code=404)

        is_active = request.data.get('is_active')
        if is_active is None:
            return error_response(message="is_active field is required.")

        user.is_active = bool(is_active)
        user.save(update_fields=['is_active'])
        return success_response(
            data=AdminUserListSerializer(user).data,
            message=f"User {'activated' if user.is_active else 'deactivated'}.",
        )
