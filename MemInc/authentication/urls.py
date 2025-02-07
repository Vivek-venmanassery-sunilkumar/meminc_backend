from django.urls import path
from .authentication_views import *

urlpatterns = [
    path('customer/', RegisterCustomer.as_view()),
    path('verifyotp/', OtpValidation.as_view()),
    path('resendotp/', ResendOtp.as_view()),
    path('vendor/', RegisterVendor.as_view()),
]

