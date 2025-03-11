from django.urls import path
from .views import *



urlpatterns = [
    path('home/', product_listing_customer_side),
    path('update-profile/', customer_profile_update),
    path('addresses/', AddressManagementCustomer.as_view()),
    path('addresses/<int:address_id>', AddressManagementCustomer.as_view()),
    path('coupons/', customer_coupons)
]


