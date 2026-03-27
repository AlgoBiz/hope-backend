# services/otp_service.py
from django.utils import timezone
from datetime import timedelta
from apps.user_account.models import OTPVerification
from apps.user_account.utils import generate_otp

OTP_EXPIRY_MINUTES = 10

def create_otp(user, purpose):
    code = generate_otp()
    expires_at = timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)

    otp = OTPVerification.objects.create(
        user=user,
        code=code,
        purpose=purpose,
        expires_at=expires_at
    )
    return otp


def verify_otp(user, code, purpose):
    try:
        otp = OTPVerification.objects.filter(
            user=user,
            code=code,
            purpose=purpose,
            is_used=False
        ).latest('created_at')
    except OTPVerification.DoesNotExist:
        return False

    if not otp.is_valid():
        return False

    otp.is_used = True
    otp.save()
    return True