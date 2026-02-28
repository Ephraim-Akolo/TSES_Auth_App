from celery import shared_task


@shared_task
def send_otp_email():
    return