from rest_framework import generics, status, permissions, exceptions as rst_exceptions
from rest_framework.response import Response
from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import (
    OTPRequestSerializer,
    OTPResponseSerializer,
    ThrottleErrorSerializer,
    OTPVerifyRequestSerializer,
    OTPVerifyResponseSerializer,
    OTPVerifyFailedResponseSerializer,
    OTPVerifyLockedResponseSerializer,
)
from .tasks import send_otp_email
from audit.tasks import write_audit_log
from audit.models import AuditLog
from .service import OTPService
from core.exceptions import RateLimitedException
from core import logger


class OTPRequestView(generics.GenericAPIView):
    '''
    Validates the user's email and enqueues an asynchronous task to send a 6-digit OTP code via email. 
    Implements rate limiting based on Email and IP address.
    '''
    serializer_class = OTPRequestSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @extend_schema(
        responses={
            202: OTPResponseSerializer,
            429: ThrottleErrorSerializer,
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
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
                    "method": request.method,
                    "path": request.path,
                    "body": request.data,
                    "client_ip_is_routable": request.client_ip_is_routable,
                }
            )
            success_serializer = OTPResponseSerializer({"expires_in": settings.OTP_TTL})
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
        

class OTPVerifyView(generics.CreateAPIView):
    '''
    Verifies the provided 6-digit code against the hashed value in Redis. 
    On success, a user record is created or updated, and JWT tokens are issued.
    '''
    serializer_class = OTPVerifyRequestSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @extend_schema(
        responses={
            200: OTPVerifyResponseSerializer,
            400: OTPVerifyFailedResponseSerializer,
            423: OTPVerifyLockedResponseSerializer,
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        otp = serializer.validated_data['otp']
        email = serializer.validated_data['email']

        try:
            result = OTPService.verify_otp(email, otp, OTPService.PURPOSE.LOGIN)

            audit_kw = {
                "email": email,
                "ip": request.client_ip,
                "user_agent": request.user_agent,
                "meta": {
                    "method": self.request.method,
                    "path": self.request.path,
                    "body": {"email": self.request.data.get("email")},
                    "client_ip_is_routable": request.client_ip_is_routable,
                }
            }

            if result.code == "200":
                user = serializer.save()
                refresh = RefreshToken.for_user(user)
                success_serializer = OTPVerifyResponseSerializer({"auth": {"refresh_token": str(refresh), "access_token": str(refresh.access_token)}})
                audit_kw['meta']['new_user'] = serializer.new_user
                write_audit_log.delay(event=AuditLog.EVENT.OTP_VERIFIED, **audit_kw)
                return Response(success_serializer.data, status=status.HTTP_200_OK)
            
            elif result.code == "400":
                logger.error(f"Error verifying OTP: {result}")
                failed_serializer = OTPVerifyFailedResponseSerializer({"attempts_left": result.attempts_left})
                write_audit_log.delay(event=AuditLog.EVENT.OTP_FAILED, **audit_kw)
                return Response(data=failed_serializer.data, status=status.HTTP_400_BAD_REQUEST)
            
            elif result.code in ("429", "423"):
                logger.error(f"Error verifying OTP: {result}")
                throttled_serializer = OTPVerifyLockedResponseSerializer({"retry_after": result.retry_after})
                write_audit_log.delay(event=AuditLog.EVENT.OTP_LOCKED, **audit_kw)
                return Response(throttled_serializer.data, status=status.HTTP_423_LOCKED)
            else:
                logger.critical(f"New status not yet implemented: {result}")
                raise NotImplementedError
            
        except Exception as exc:
            logger.critical(f"Error verifying OTP: {exc}")
            raise rst_exceptions.APIException("Sorry, something went wrong on our end!")


