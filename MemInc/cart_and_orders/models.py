from django.db import models
from authentication.models import CustomUser,Customer
from vendor_side.models import ProductVariants
from admin_side.models import Coupon
from decimal import Decimal
from wallet.models import WalletTransactionCustomer,WalletTransactionsAdmin, Wallet
from django.contrib.auth import get_user_model
from django.utils import timezone

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

        original_discount_price = self.discount_price
        has_payment = hasattr(self, 'order_payment')


        for item in items:
            if item.order_item_status == 'cancelled':
                order = item.order
                order.total_price -= item.price
                order.save()
                # Track the original discount value before resetting it

                if self.coupon and self.coupon.min_order_value:
                    if self.total_price < self.coupon.min_order_value:
                        self.discount_price = Decimal('0.00')
                        self.save()

                # Handle refund logic
                if has_payment and self.order_payment.payment_status == 'completed' and self.order_payment.payment_method != 'cod':
                    refund_amount = item.price

                    # Use the original discount value for refund calculation
                    if original_discount_price > 0:
                        refund_amount -= original_discount_price
                        self.discount_price = Decimal('0.00')
                        self.save()

                    # Credit the refund amount to the customer's wallet
                    if not hasattr(self.customer.user, 'wallet'):
                        # Create a wallet if it doesn't exist
                        Wallet.objects.create(user=self.customer.user)
                    wallet = self.customer.user.wallet
                    wallet.credit(amount = refund_amount)
                    WalletTransactionCustomer.objects.create(
                        user=self.customer.user,
                        amount=refund_amount,
                        transaction_type='credit',
                        transaction_id=f"REFUND_{self.id}_{item.id}_{timezone.now()}"
                    )
                    #admin wallet update pending
                    admin = User.objects.get(role = 'admin')
                    admin_wallet, created = Wallet.objects.get_or_create(user = admin)
                    admin_wallet.debit(amount = refund_amount)
                    admin_wallet_transaction = WalletTransactionsAdmin.objects.create(
                        user = admin,
                        amount = refund_amount,
                        transaction_type = 'debit',
                        transaction_through = 'wallet',
                        transacted_user = self.customer.user
                    )
                    item.refund_amount = refund_amount
                    item.refund_status = 'processed'
                    item.save() 
        non_cancelled_items = [item for item in items if item.order_item_status != 'cancelled']

        # Determine the overall order status based on non-cancelled items
        if not non_cancelled_items:
            # All items are cancelled
            self.order_status = 'cancelled'
        elif all(item.order_item_status == 'delivered' for item in non_cancelled_items):
            # All non-cancelled items are delivered
            self.order_status = 'delivered'
        elif all(item.order_item_status == 'dispatched' for item in non_cancelled_items):
            # All non-cancelled items are dispatched
            self.order_status = 'dispatched'
        elif any(item.order_item_status == 'cancelled' for item in items):
            # Some items are cancelled, but not all non-cancelled items are delivered/dispatched
            self.order_status = 'cancelled'
        else:
            # Default to processing
            self.order_status = 'processing'
            self.save(update_fields = ['order_status'])

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
    cancel_time = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.order_item_status:
            self.order_item_status = self.order_item_status.lower()
        self.price = self.variant.price * self.quantity
        super().save(*args, **kwargs)
       

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


