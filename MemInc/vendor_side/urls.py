from django.urls import path
from .views import *

urlpatterns = [
    path('add-product/', Product_create_view.as_view()),
]