from rest_framework import serializers
from .models import AuditLog


class AuditLogsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = "__all__"