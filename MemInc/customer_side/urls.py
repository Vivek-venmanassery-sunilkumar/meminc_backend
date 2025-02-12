from django.urls import path
from .views import *



urlpatterns = [
    path('home/', product_listing_customer_side)
]


