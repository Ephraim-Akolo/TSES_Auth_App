from django.db import models
from uuid import uuid4

class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    event = models.CharField(max_length=50)
    email = models.EmailField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email} - {self.event} at {self.created_at}"