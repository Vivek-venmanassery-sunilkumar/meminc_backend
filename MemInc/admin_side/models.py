from django.db import models

# Create your models here.

class Coupon(models.Model):
    expiry_time = models.DateTimeField()
    coupon_type = models.CharField(max_length=100)
    max_discount = models.DecimalField(max_digits=10, decimal_places=2)
    min_order_value = models.DecimalField(max_digits=10, decimal_places=2)