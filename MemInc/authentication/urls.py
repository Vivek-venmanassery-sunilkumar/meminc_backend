from django.urls import path
from .authentication_views import *

urlpatterns = [
    path('customer/', RegisterCustomer.as_view())
]

