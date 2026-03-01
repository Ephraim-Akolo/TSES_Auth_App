from django_filters import rest_framework as filters
from .models import AuditLog


class AuditLogFilter(filters.FilterSet):
    from_date = filters.DateTimeFilter(field_name="created_at", lookup_expr='gte')
    to_date = filters.DateTimeFilter(field_name="created_at", lookup_expr='lte')
    email = filters.CharFilter(lookup_expr='icontains')
    event = filters.ChoiceFilter(choices=AuditLog.EVENT.choices)

    class Meta:
        model = AuditLog
        fields = ['email', 'event', 'from_date', 'to_date']