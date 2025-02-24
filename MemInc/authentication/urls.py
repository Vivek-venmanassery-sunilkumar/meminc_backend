from django.urls import path, include
from .authentication_views import *

urlpatterns = [
    path('customer/', RegisterCustomer.as_view()),
    path('verifyotp/', OtpValidation.as_view()),
    path('resendotp/', ResendOtp.as_view()),
    path('vendor/', RegisterVendor.as_view()),
    path('login/', LoginView.as_view()),
    path('logout/', logout),
    path('google/',GoogleLoginView.as_view(), name = 'google_login'),
    path('password-reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
]

