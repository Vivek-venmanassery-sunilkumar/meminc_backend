"""
URL configuration for MemInc project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from django.conf.urls.static import static
from . import settings

urlpatterns = [
    path('register/', include('authentication.urls')),
    path('admin/', include('admin_side.urls')),
    path('vendor/', include('vendor_side.urls')),
    path('customer/', include('customer_side.urls')),
    path('cart/', include('cart_and_orders.urls')),
] + static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
