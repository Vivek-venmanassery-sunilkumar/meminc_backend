from django.urls import path
from .views import *



urlpatterns = [
    path('customer/', customer_wallet_credit),
    path('customer/update-balance/', customer_wallet_credit_callback),
    path('customer/wallet-balance/', customer_wallet_balance_fetch),
    path('admin/', admin_wallet_balance_fetch),
    path('admin-transactions/', admin_wallet_transactions_fetch),
    path('customer-transactions/', customer_wallet_transactons_fetch),
]