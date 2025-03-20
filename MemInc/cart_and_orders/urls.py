from django.urls import path
from .views import *

urlpatterns = [
    path('',CartDetails.as_view()),
    path('<int:variant_id>', CartDetails.as_view()),   
    path('checkout/', Checkout.as_view()),
    path('razorpay-callback/', RazorpayCallback.as_view()),
    path('retry-payment/', retry_payment),
    path('wishlist/', WishListFunctions.as_view()),
    path('wishlist/<int:variant_id>/', WishListFunctions.as_view())
]
