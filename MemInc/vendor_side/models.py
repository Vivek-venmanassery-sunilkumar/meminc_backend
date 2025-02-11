from django.db import models
from authentication.models import Vendor

# Create your models here.


class Categories(models.Model):
    category = models.CharField(max_length=20)
    is_enabled = models.BooleanField(default=True)


class Products(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete = models.CASCADE, related_name= 'vendor_products')
    category = models.ForeignKey(Categories,on_delete=models.CASCADE,related_name='product_profile')
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=200)
    variant_unit = models.CharField(max_length=10)
    image = models.ImageField(upload_to='products/')


    def __str__(self):
        return f"{self.name}"

class Product_variants(models.Model):
    product = models.ForeignKey(Products, on_delete=models.CASCADE, related_name='variant_profile')
    quantity = models.IntegerField()
    price = models.IntegerField()
    stock = models.IntegerField()

