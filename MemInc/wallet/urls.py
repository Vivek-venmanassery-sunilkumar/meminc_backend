from django.urls import path
from .views import *



urlpatterns = [
    path('customer/', customer_wallet_credit),
    path('customer/update-balance/', customer_wallet_credit_callback),
    path('customer/wallet-balance/', customer_wallet_balance_fetch)
]