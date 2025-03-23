from django.urls import path
from .views import *


urlpatterns = [
    path('customers/', list_customer),
    path('vendors/', list_vendor),
    path('block_user/',block_user),
    path('verify-seller/', verify_vendor),
    path('categories/', Categoryview.as_view()),
    path('categories/<int:id>/',Categoryview.as_view()),
    path('coupons/', Coupons.as_view()),
    path('coupons/<int:coupon_id>/', Coupons.as_view()),
    path('coupons/<int:coupon_id>/toggle/', toggle),
    path('orders/', admin_order_fetch),
    path('order-status-update/<int:order_item_id>/', admin_order_status_update),
    path('dashboard/', dashboardfetch),
    path('salesreport/', order_details_salesreport)
]