from django.urls import path
from .views import *


urlpatterns = [
    path('customers/', list_customer),
    path('vendors/', list_vendor),
]