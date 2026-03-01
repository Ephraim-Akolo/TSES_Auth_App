from celery import shared_task
from django.db import DatabaseError
from core import logger
from .models import AuditLog


@shared_task(
    bind=True,
    autoretry_for=(DatabaseError, ConnectionError),
    retry_backoff=True,
    max_retries=3
)
def write_audit_log(self, event, email, ip, user_agent, meta=None):
    """
    Asynchronously inserts an AuditLog row.
    """
    if meta is None:
        meta = {}

    logger.info(f"Logging event '{event}' for {email}")
    try:
        AuditLog.objects.create(
            event=event,
            email=email,
            ip_address=ip,
            user_agent=user_agent,
            metadata=meta
        )
        return f"Audit log created: {event} for {email}"
    except (DatabaseError, ConnectionError) as exc:
        logger.error(f"Database error while writing audit log: {exc}")
        raise
    except Exception as exc:
        logger.critical(f"Unexpected error in write_audit_log: {exc}")
        raise