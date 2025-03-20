from django.urls import path
from .views import *

urlpatterns = [
    path('add-product/', Product_create_view.as_view()),
    path('product-listing/', product_listing_vendor),
    path('update-profile/', vendor_profile_update),
    path('products/<int:product_id>/',ProductDetailsEdit.as_view()),
    path('orders/', vendor_order),
    path('order-status-update/<int:order_item_id>/', vendor_order_status_update),
    path('brands/', brands_fetch),
]