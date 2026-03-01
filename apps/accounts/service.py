import redis
import secrets
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from core.exceptions import RateLimitedException
from enum import StrEnum
from dataclasses import dataclass
from typing import Optional


redis_client = redis.from_url(settings.REDIS_URL)


class OTPService:
    OTP_TTL = settings.OTP_TTL
    OTP_MAX_ATTEMPTS = settings.OTP_MAX_ATTEMPTS
    OTP_MAX_ATTEMPTS_TTL = settings.OTP_MAX_ATTEMPTS_TTL
    OTP_CODE_LENGTH = settings.OTP_CODE_LENGTH
    OTP_RATE_LIMIT_EMAIL = settings.OTP_RATE_LIMIT_EMAIL
    OTP_RATE_WINDOW_EMAIL = settings.OTP_RATE_WINDOW_EMAIL
    OTP_RATE_LIMIT_IP = settings.OTP_RATE_LIMIT_IP
    OTP_RATE_WINDOW_IP = settings.OTP_RATE_WINDOW_IP

    class PURPOSE(StrEnum):
        LOGIN = 'login'

    @staticmethod
    def _is_rate_limited(key:str, limit:int, window:int):
        """
        Redis rate limiting using atomic counter.
        """
        count = redis_client.incr(key)

        if count == 1:
            redis_client.expire(key, window)

        if count > limit:
            ttl = redis_client.ttl(key)
            return True, max(ttl, 0)

        return False, 0
    
    @staticmethod
    def _get_email_rate_key(email:str):
        return f"otp_email_rate:{email}"
    
    @staticmethod
    def _get_ip_rate_key(ip:str):
        return f"otp_ip_rate:{ip}"
    
    @staticmethod
    def _get_redis_otp_key(email:str, purpose:str):
        return f"otp:{email}:{purpose}"
    
    @staticmethod
    def _get_otp_attempts_key(email:str, purpose:str):
        return f"otp_attempts:{email}:{purpose}"
    
    @staticmethod
    def _get_lockout_key(email:str):
        return f"otp_lockout:{email}"

    @classmethod
    def generate_otp(cls, length:int=None):
        """
        Generates OTP Code of length if provided, otherwise default to length from settings.
        """
        code_length = length or cls.OTP_CODE_LENGTH
        digits = "0123456789"
        return "".join(secrets.choice(digits) for _ in range(code_length))
    
    @classmethod
    def create_otp(cls, email:str, ip:str, purpose:PURPOSE=PURPOSE.LOGIN):
        """
        Creates OTP with Redis TTL and rate limiting.
        """

        email_key = cls._get_email_rate_key(email)
        ip_key = cls._get_ip_rate_key(ip)

        limited, retry = cls._is_rate_limited(email_key, cls.OTP_RATE_LIMIT_EMAIL, cls.OTP_RATE_WINDOW_EMAIL)
        if limited:
            raise RateLimitedException(retry, "Too many OTP requests from this email")
        
        limited, retry = cls._is_rate_limited(ip_key, cls.OTP_RATE_LIMIT_IP, cls.OTP_RATE_WINDOW_IP)
        if limited:
            raise RateLimitedException(retry, "Too many OTP requests from this IP")

        otp = cls.generate_otp()

        redis_key = cls._get_redis_otp_key(email, purpose)

        redis_client.setex(
            redis_key,
            cls.OTP_TTL,
            make_password(otp)
        )

        redis_client.delete(cls._get_otp_attempts_key(email, purpose)) # Reset attempt counter

        return otp
    
    @classmethod
    def verify_otp(cls, email:str, otp:str, purpose:PURPOSE=PURPOSE.LOGIN):
        """
        Verifies OTP Code with Redis.
        """
        redis_key = cls._get_redis_otp_key(email, purpose)
        attempts_key = cls._get_otp_attempts_key(email, purpose)
        lockout_key = cls._get_lockout_key(email)

        lockout_ttl = redis_client.ttl(lockout_key)
        if lockout_ttl > 0:
            return OTPResult(
                status='error',
                code="423",
                message="Locked",
                retry_after=lockout_ttl,
            )

        stored_hash = redis_client.get(redis_key)

        # if not stored_hash:
        #     return OTPResult(
        #         status='error',
        #         code="404",
        #         message="OTP expired or not found"
        #     )

        attempts = redis_client.incr(attempts_key)

        if attempts == 1:
            redis_client.expire(attempts_key, cls.OTP_MAX_ATTEMPTS_TTL)

        if attempts > cls.OTP_MAX_ATTEMPTS:
            lockout_ttl = redis_client.ttl(attempts_key)
            redis_client.setex(lockout_key, lockout_ttl, "locked")
            redis_client.delete(redis_key)
            return OTPResult(
                status='error',
                code="429",
                message="Too many attempts",
                retry_after = lockout_ttl,
            )

        if not stored_hash or not check_password(otp, stored_hash.decode('utf-8')):
            return OTPResult(
                status='error',
                code="400",
                message="Invalid OTP",
                attempts_left=cls.OTP_MAX_ATTEMPTS - attempts
            )

        redis_client.delete(redis_key)
        redis_client.delete(attempts_key)

        return OTPResult(
            status='success',
            code="200",
            message="OTP verified",
        )


@dataclass
class OTPResult:
    status: str
    code: str
    message: str
    retry_after: Optional[int] = None
    attempts_left:Optional[int] = None
    
