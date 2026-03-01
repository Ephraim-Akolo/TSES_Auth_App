from django.db import models
from uuid import uuid4


class AuditLog(models.Model):
    class EVENT(models.TextChoices):
        OTP_REQUESTED = ('OTP_REQUESTED', 'OTP Requested')
        OTP_VERIFIED = ('OTP_VERIFIED', 'OTP Verified')
        OTP_FAILED = ('OTP_FAILED', 'OTP Failed')
        OTP_LOCKED = ('OTP_LOCKED', 'OTP locked')
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    event = models.CharField(max_length=50, choices=EVENT.choices, db_index=True)
    email = models.EmailField(db_index=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', '-created_at']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.email} - {self.event} at {self.created_at}"