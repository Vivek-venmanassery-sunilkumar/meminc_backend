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
    path('salesreport/', order_details_salesreport),
    path('banner/', add_banner),
    path('fetch-banner/', banner_fetch),
    path('banner-remove/<int:banner_id>/', banner_remove),
    path('banner-update/<int:banner_id>/', banner_update),
    path('products-fetch/', admin_product_fetch),
    path('block-product/<int:product_id>/', admin_product_block)
]

