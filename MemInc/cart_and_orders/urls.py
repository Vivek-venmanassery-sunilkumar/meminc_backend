from django.urls import path
from .views import *

urlpatterns = [
    path('',CartDetails.as_view()),
    path('<int:variant_id>', CartDetails.as_view()),   
]
