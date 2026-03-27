from django.core.mail import EmailMultiAlternatives
from django.conf import settings


def send_otp_email(email, otp, purpose='verify'):
    subject_map = {
        'verify': 'Verify your Hope account',
        'password_reset': 'Reset your Hope password',
    }
    action_map = {
        'verify': 'verify your email address',
        'password_reset': 'reset your password',
    }
    subject = subject_map.get(purpose, 'Your OTP Code')
    action = action_map.get(purpose, 'complete your request')

    text_body = f"Your OTP code is: {otp}\n\nThis code expires in 10 minutes."

    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;padding:32px;border:1px solid #eee;border-radius:8px;">
        <h2 style="color:#1a1a1a;">My Hope Story</h2>
        <p style="color:#444;">Use the code below to {action}:</p>
        <div style="font-size:36px;font-weight:bold;letter-spacing:8px;text-align:center;
                    padding:24px;background:#f5f5f5;border-radius:6px;margin:24px 0;color:#1a1a1a;">
            {otp}
        </div>
        <p style="color:#888;font-size:13px;">This code expires in <strong>10 minutes</strong>. Do not share it with anyone.</p>
        <hr style="border:none;border-top:1px solid #eee;margin:24px 0;">
        <p style="color:#bbb;font-size:12px;">If you didn't request this, you can safely ignore this email.</p>
    </div>
    """

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email],
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send()
