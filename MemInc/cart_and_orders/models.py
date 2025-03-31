from django.db import models
from authentication.models import CustomUser,Customer
from vendor_side.models import ProductVariants
from admin_side.models import Coupon
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction

User = get_user_model()
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

class WishList(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='wishlist')


class WishListItems(models.Model):
    wishlist = models.ForeignKey(WishList, on_delete=models.CASCADE, related_name='wishlist_items')
    variant = models.ForeignKey(ProductVariants, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)



class Order(models.Model):
    customer= models.ForeignKey(Customer, on_delete=models.CASCADE, related_name = 'customer_order_details')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    coupon = models.ForeignKey(Coupon, blank=True, null=True, on_delete=models.SET_NULL)
    discount_price =models.DecimalField(max_digits=10, decimal_places=2, default= Decimal(0.00))
    final_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    order_status = models.CharField(max_length=100,default='Processing')
    
    
    def save(self, *args, **kwargs):
        self.final_price = self.total_price-self.discount_price
        super().save(*args, **kwargs)

    def update_order_status(self):
        with transaction.atomic():
            items = self.order_items.select_for_update().all()
            if not items.exists():
                self.order_status = 'Processing'
                self.save()
                return
            non_cancelled_items = [item for item in items if item.order_item_status != 'cancelled']

            #Determine order status
            if not non_cancelled_items:
                self.order_status = 'cancelled'
            elif all(item.order_item_status == 'delivered' for item in non_cancelled_items):
                self.order_status = 'delivered'
            elif all(item.order_item_status == 'dispatched' for item in non_cancelled_items):
                self.order_status = 'dispatched'
            else:
                self.order_status = 'Processing'
            
            self.save(update_fields = ['order_status'])
    
    def process_refund(self, order_item):

        from wallet.models import WalletTransactionCustomer,WalletTransactionsAdmin, Wallet
        """Handle refund logic for a cancelled item"""
        if order_item.refund_status == 'processed':
            return 
        
        with transaction.atomic():
            payment = getattr(self, 'order_payment', None)
            if not payment or payment.payment_status != 'completed':
                return

            refund_amount = order_item.price
            original_discount = self.discount_price

            if self.coupon:
                remaining_items = self.order_items.exclude(id=order_item.id)
                remaining_total_price = sum(item.price for item in remaining_items if item.order_item_status != 'cancelled')

                if remaining_total_price < self.coupon.min_order_value:
                    refund_amount -= original_discount
                    self.discount_price = Decimal('0.00')
                    self.save()
            #Adjust discount if coupon minimum value is no longer met
            if self.coupon and self.total_price < self.coupon.min_order_value:
                refund_amount -= original_discount
                self.discount_price = Decimal('0.00')
                self.total_price -= order_item.price
                self.save()
            
            # Process wallet transactions
            customer_wallet, _ = Wallet.objects.get_or_create(user = self.customer.user)
            admin = User.objects.get(role = 'admin')
            admin_wallet, _ = Wallet.objects.get_or_create(user = admin)

            #Credit customer wallet
            customer_wallet.credit(refund_amount)
            WalletTransactionCustomer.objects.create(
                user = self.customer.user,
                amount = refund_amount,
                transaction_type = 'credit',
                transaction_id = f"Refund_{self.id}_{order_item.variant.product.name}_{timezone.now().timestamp()}"
            )

            # Debit admin wallet
            admin_wallet.debit(refund_amount)
            WalletTransactionsAdmin.objects.create(
                user=admin,
                amount = refund_amount,
                transaction_type = 'debit',
                transaction_through = 'wallet',
                transacted_user = self.customer.user
            )

            order_item.refund_amount = refund_amount
            order_item.refund_status = 'processed'
            order_item.save()
        
    def are_all_payments_done_to_vendor(self):
        non_cancelled_items = self.order_items.exclude(order_item_status = 'cancelled')
        if not non_cancelled_items.exists():
            return False
        
        return all(item.is_payment_done_to_vendor for item in non_cancelled_items)

class OrderItems(models.Model):
    ORDER_ITEM_STATUS_CHOICES = [
        ('processing', 'Processing'),
        ('dispatched', 'Dispatched'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    variant = models.ForeignKey(ProductVariants, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    order_item_status = models.CharField(max_length=100,choices=ORDER_ITEM_STATUS_CHOICES, default='processing')
    cancel_reason = models.CharField(max_length=150, blank = True)
    refund_status = models.CharField(max_length=100, blank=True, null=True)
    refund_amount = models.DecimalField(max_digits = 10, decimal_places = 2, null=True, blank=True)
    is_payment_done_to_vendor = models.BooleanField(default=False)
    payment_done_to_vendor = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cancel_time = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        self.price = self.variant.price * self.quantity
        
        if self.pk:
            previous_status = OrderItems.objects.get(pk = self.pk).order_item_status
        else:
            previous_status = None
        
        if self.order_item_status == 'delivered' and previous_status != 'delivered':
            self.delivered_at = timezone.now()
        
        super().save(*args, **kwargs)
        if self.order_item_status == 'cancelled':
            self.order.process_refund(self)
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


