from celery import shared_task


@shared_task
def write_audit_log():
    return