from django.db import models
from authentication.models import CustomUser,Customer
from vendor_side.models import ProductVariants
from admin_side.models import Coupon
from decimal import Decimal
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





class Order(models.Model):
    customer= models.ForeignKey(Customer, on_delete=models.CASCADE, related_name = 'customer_order_details')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    coupon = models.ForeignKey(Coupon, blank=True, null=True, on_delete=models.SET_NULL)
    discount_price =models.DecimalField(max_digits=10, decimal_places=2, default= Decimal(0.00))
    final_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    order_status = models.CharField(max_length=100,default='Processing')
    cancel_reason = models.CharField(max_length=150, blank=True)
    cancel_time = models.DateTimeField(null=True, blank=True)
    
    
    def save(self, *args, **kwargs):
        self.final_price = self.total_price-self.discount_price
        super().save(*args, **kwargs)

    def update_order_status(self):

        items = self.order_items.all()
        if all(item.order_item_status == 'Shipped' for item in items):
            self.order_status ='Shipped'
        elif all(item.order_item_status == 'Delivered' for item in items):
            self.order_status = 'Delivered'
        elif any(item.order_item_status == 'Cancelled' for  item in items):
            self.order_status = 'Partially Cancelled'
        else:
            self.order_status = 'Processing'
        
        self.save(update_fields = ['order_status'])

class OrderItems(models.Model):
    ORDER_ITEM_STATUS_CHOICES = [
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    variant = models.ForeignKey(ProductVariants, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    order_item_status = models.CharField(max_length=100,choices=ORDER_ITEM_STATUS_CHOICES, default='processing')
    cancel_reason = models.CharField(max_length=150, blank = True)
    cancel_time = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.order_item_status:
            self.order_item_status = self.order_item_status.lower()
        self.price = self.variant.price * self.quantity
        super().save(*args, **kwargs)
        self.order.update_order_status()

class Payments(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='order_payment')
    payment_method = models.CharField(max_length=100)
    payment_status = models.CharField(max_length=100, default= 'pending')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    

class ShippingAddress(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name = 'customer_shipping_address')
    name = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=12, blank=True, null=True)
    street_address = models.CharField(max_length=100, blank = False, null=False)
    city = models.CharField(max_length=100, blank=False, null=False)
    state = models.CharField(max_length=100, blank=False, null=False)
    country = models.CharField(max_length=100, blank=False, null=False)
    pincode = models.CharField(max_length=20, blank=False, null=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_shipping_address')

    def __str__(self):
        return f"{self.street_address}, {self.city}, {self.state}, {self.country}"


