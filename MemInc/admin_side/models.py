from django.db import models
from enum import Enum
from django.contrib.auth import get_user_model

user = get_user_model()

# Create your models here.

class DiscountType(Enum):
    FLAT = 'flat'
    PERCENTAGE = 'percentage'

    @classmethod
    def choices(cls):
        return [(key.value, key.name.title()) for key in cls]


class Coupon(models.Model):
    code = models.CharField(max_length=100)
    start_date = models.DateField()
    expiry_date = models.DateField()
    discount_type = models.CharField(max_length=100, choices= DiscountType.choices())
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    max_discount = models.DecimalField(max_digits=10, decimal_places=2)
    min_order_value = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField()
    is_active_admin = models.BooleanField(default = True)


    def __str__(self):
        return f"{self.discount_type} - {self.discount_value}"


class UsedCoupon(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    user = models.ForeignKey(user, on_delete=models.CASCADE, related_name='used_coupon')


class Banner(models.Model):
    image = models.ImageField(upload_to='banners/', null=True, blank=True)
    start_date = models.DateField()
    expiry_date = models.DateField()
    is_active = models.BooleanField()
    is_active_admin = models.BooleanField(default = True)
