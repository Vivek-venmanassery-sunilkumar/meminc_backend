from django.urls import path
from .views import *

urlpatterns = [
    path('add-product/', Product_create_view.as_view()),
    path('product-listing/', product_listing_vendor),
    path('update-profile/', vendor_profile_update),
    path('products/<int:product_id>/',ProductDetailsEdit.as_view()),
]