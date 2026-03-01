from rest_framework import generics, status, permissions, exceptions as rst_exceptions
from rest_framework.response import Response
from django.conf import settings
from drf_spectacular.utils import extend_schema
from .serializers import (
    OTPRequestSerializer,
    OTPResponseSerializer,
    ThrottleErrorSerializer,
)
from .tasks import send_otp_email
from audit.tasks import write_audit_log
from audit.models import AuditLog
from .service import OTPService
from core.exceptions import RateLimitedException
from core import logger


class OTPRequestView(generics.GenericAPIView):
    serializer_class = OTPRequestSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @extend_schema(
        # request=OTPRequestSerializer,
        responses={
            202: OTPResponseSerializer,
            429: ThrottleErrorSerializer,
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = OTPRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.validated_data['email']
        PURPOSE = OTPService.PURPOSE

        try:
            otp = OTPService.create_otp(email, request.client_ip, PURPOSE.LOGIN)
            send_otp_email.delay(email, otp)
            write_audit_log.delay(
                event=AuditLog.EVENT.OTP_REQUESTED,
                email=email,
                ip=request.client_ip,
                user_agent=request.user_agent,
                meta={
                    "method": self.request.method,
                    "path": self.request.path,
                    "body": self.request.data,
                    "client_ip_is_routable": request.client_ip_is_routable,
                }
            )
            success_serializer = OTPResponseSerializer({"message": "Success", "expires_in": settings.OTP_TTL})
            return Response(data=success_serializer.data, status=status.HTTP_202_ACCEPTED)
        except RateLimitedException as exc:
            logger.error(f"RateLimitedException: {exc}")
            error_serializer = ThrottleErrorSerializer({
                "error": exc.detail.get('message'),
                "retry_after": exc.detail.get('retry_after')
            })
            return Response(data=error_serializer.data, status=status.HTTP_429_TOO_MANY_REQUESTS)
        except Exception as exc:
            logger.critical(f"Error creating otp: {exc}")
            raise rst_exceptions.APIException("Sorry, something went wrong on our end!")
        
