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


    def __str__(self):
        return f"{self.name}"

class ProductVariants(models.Model):
    product = models.ForeignKey(Products, on_delete=models.CASCADE, related_name='variant_profile')
    quantity = models.IntegerField()
    variant_unit = models.CharField(max_length=10, default = 'kg')
    price = models.DecimalField(decimal_places=2, max_digits=5)
    stock = models.IntegerField()

class ProductImages(models.Model):
    product = models.ForeignKey(Products, on_delete = models.CASCADE, related_name = 'product_images')
    image = models.ImageField(upload_to='products/')

    

