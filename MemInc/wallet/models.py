from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal
from cart_and_orders.models import OrderItems,Order
# Create your models here.


User = get_user_model()


class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name = 'wallet')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default = 0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.first_name} - ₹{self.balance}"
    
    def credit(self, amount):
        self.balance = Decimal(self.balance) + Decimal(amount)
        self.save()

    def debit(self, amount):
        if self.balance >= amount:
            self.balance -= amount
            self.save()
            return True
        return False
    
class WalletTransactionCustomer(models.Model):
    Transaction_Types = [
        ('credit', 'Credit'),
        ('debit', 'Debit')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name = 'wallet_transactions_customer')
    amount = models.DecimalField(max_digits = 12, decimal_places=2)
    transaction_type = models.CharField(choices= Transaction_Types, max_length = 10)
    transaction_id = models.CharField(blank = True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.transaction_type} - ₹{self.amount}"
    

class WalletTransactionsAdmin(models.Model):
    Transaction_Types = [
        ('credit', 'Credit'),
        ('debit', 'Debit')
    ]
    Transaction_Through_Types = [
        ('bank','Bank'),
        ('wallet', 'Wallet'),
        ('cash', 'Cash')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name = 'wallet_transactions_admin')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(choices=Transaction_Types, max_length = 100)
    transaction_through = models.CharField(choices = Transaction_Through_Types, max_length=100)
    transacted_user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add = True)

    def __str__(self):
        return f"{self.user.email} - {self.transaction_type} -₹{self.amount}"

class WalletTransactionsVendor(models.Model):
    class Meta:
        unique_together = ('order_item', 'transaction_type')

    Transaction_Types = [
        ('credit','Credit')
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wallet_transactions_vendor')
    order_item = models.ForeignKey(OrderItems, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(choices = Transaction_Types)
    transaction_through = models.CharField(default = 'wallet')
    transacted_user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add = True)

class CommissionRecievedAdminPerOrder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_commission_per_orderitem')
    commission_needed_to_be_kept = models.DecimalField(max_digits=12, decimal_places=2)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    is_discount_present = models.BooleanField(default = True)
    commission_kept = models.DecimalField(max_digits=12, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    