from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from smtplib import SMTPException
from core import logger


@shared_task(
    bind=True,
    autoretry_for=(SMTPException, ConnectionError), 
    retry_backoff=True, 
    max_retries=5,
    retry_jitter=True
)
def send_otp_email(self, email: str, otp: str):
    """
    Asynchronously sends the OTP to the user's email.
    """
    logger.info(f"Attempting to send OTP to {email}. Attempt {self.request.retries + 1}")
    subject = 'Verification Code'
    message = f'Your one-time password is: {otp}. It expires in {settings.OTP_TTL//60} minutes.'
    email_from = settings.DEFAULT_FROM_EMAIL
    try:
        send_mail(subject, message, email_from, [email], fail_silently=False)
        logger.info(f"Successfully sent OTP email to {email}")
        return f"Email sent to {email}"
    except (SMTPException, ConnectionError) as exc:
        logger.error(f"Transient error sending email to {email}: {exc}")
        raise
    except Exception as exc:
        logger.critical(f"Non-recoverable error sending email to {email}: {exc}")
        raise