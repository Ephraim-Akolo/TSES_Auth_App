from rest_framework import serializers
from .models import User


class OTPRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, help_text="User's email address for OTP delivery")

    def validate_email(self, value):
        return value.lower().strip()


class OTPResponseSerializer(serializers.Serializer):
    message = serializers.CharField(default="Success")
    expires_in = serializers.IntegerField(help_text="TTL in seconds")


class ThrottleErrorSerializer(serializers.Serializer):
    error = serializers.CharField()
    retry_after = serializers.IntegerField(help_text="Seconds to wait")


class OTPVerifyRequestSerializer(serializers.ModelSerializer):
    otp = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)

    class Meta:
        model = User
        fields = ['email', 'otp']

    def validate_email(self, value):
        return value.lower().strip()
    
    def create(self, validated_data):
        user, created =  User.objects.update_or_create(email=validated_data['email'])
        self.new_user = created
        return user
    

class AccessTokenSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    

class OTPVerifyResponseSerializer(serializers.Serializer):
    message = serializers.CharField(default='Login successful')
    auth = AccessTokenSerializer()


class OTPVerifyFailedResponseSerializer(serializers.Serializer):
    message = serializers.CharField(default="Invalid OTP")
    attempts_left = serializers.IntegerField()


class OTPVerifyLockedResponseSerializer(serializers.Serializer):
    message = serializers.CharField(default="Too many failed attempts.")
    retry_after = serializers.IntegerField()


