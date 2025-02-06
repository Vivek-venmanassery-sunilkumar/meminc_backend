from django.urls import path
from .authentication_views import *

urlpatterns = [
    path('customer/', RegisterCustomer.as_view()),
    path('customer/verifyotp/', CustomerOtpValidation.as_view()),
    path('customer/resendotp/', ResendOtp.as_view())
]

