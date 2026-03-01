from django.urls import path
from . import views


urlpatterns = [
    path('logs', views.AuditLogsView.as_view(), name='audit-logs'),
]