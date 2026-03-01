from rest_framework import serializers


class OTPRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, help_text="User's email address for OTP delivery")

    def validate_email(self, value):
        return value.lower().strip()


class OTPResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    expires_in = serializers.IntegerField(help_text="TTL in seconds")


class ThrottleErrorSerializer(serializers.Serializer):
    error = serializers.CharField()
    retry_after = serializers.IntegerField(help_text="Seconds to wait")

