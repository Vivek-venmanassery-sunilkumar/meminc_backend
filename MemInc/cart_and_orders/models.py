from django.db import models
from authentication.models import CustomUser
from vendor_side.models import ProductVariants
# Create your models here.

class Cart(models.Model):
    user= models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='cart')

    def calculate_total_price(self):
        total_price = sum(item.variant.price * item.quantity for item in self.items.all())
        return total_price



class CartItems(models.Model):
    cart = models.ForeignKey(Cart, on_delete = models.CASCADE, related_name='items')
    variant = models.ForeignKey(ProductVariants, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default = 1)