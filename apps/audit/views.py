from rest_framework import generics, filters as drf_filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import AuditLog
from .serializers import AuditLogsSerializer
from .filters import AuditLogFilter


class AuditLogsView(generics.ListAPIView):
    '''
    Retrieves a paginated list of all authentication-related events. 
    Supports filtering by email, event type, and date range.
    '''
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogsSerializer
    filter_backends = [DjangoFilterBackend, drf_filters.OrderingFilter]
    filterset_class = AuditLogFilter
    ordering_fields = ['created_at', 'event']
    
