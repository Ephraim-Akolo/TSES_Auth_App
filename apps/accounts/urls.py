from django.urls import path
from . import views


urlpatterns = [
    path('otp/request', views.OTPRequestView.as_view(), name='otp-request'),
    path('otp/verify', views.OTPVerifyView.as_view(), name='otp-verify'),
]