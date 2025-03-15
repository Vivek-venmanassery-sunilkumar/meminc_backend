from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal
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