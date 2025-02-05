from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user= self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self,email,password, **extra_fields):
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')

        return self.create_user(email,password,**extra_fields)

class CustomUser(AbstractBaseUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('customer','Customer'),
        ('vendor', 'Vendor'),
    ]
    
    email = models.EmailField(unique = True)
    role = models.CharField(max_length=20, choices = ROLE_CHOICES, default='customer')
    is_active = models.BooleanField(default = True)
    is_superuser = models.BooleanField(default = False)
    is_blocked = models.BooleanField(default = False)
    created_at = models.DateTimeField(default = timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

class Customer(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name = 'customer_profile')
    first_name = models.CharField(max_length = 100)
    last_name = models.CharField(max_length= 100)
    phone_number = models.CharField(max_length=15, unique=True)
    is_verified = models.BooleanField(default = False)

    def save(self, *args, **kwargs):
        if not self.user.is_blocked:
            self.user.is_active = True
        else:
            self.user.is_active = False
        self.user.save()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    


class Vendor(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='vendor_profile')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    company_name = models.CharField(max_length=200, unique=True)
    phone_number = models.CharField(max_length=15)
    is_verified = models.BooleanField(default = False)

    @property
    def is_active(self):
        return self.is_verified and self.user.is_active
    
    def save(self, *args, **kwargs):
        if self.is_verified and not self.user.is_blocked:
            self.user.is_active = True
        else:
            self.user.is_active = False

        self.user.save()
        super().save(*args, **kwargs)
    
class CustomerAddress(models.Model):
    customer = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name = 'customer_addresses')
    street_address = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    pincode = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.street_address}, {self.city}, {self.state}, {self.country}"
class VendorAddress(models.Model):
    vendor = models.OneToOneField(get_user_model(), on_delete = models.CASCADE, related_name = 'vendor_address')
    street_address = models.CharField(max_length = 100)
    city = models.CharField(max_length = 100)
    state = models.CharField(max_length = 100)
    country = models.CharField(max_length = 100)
    pincode = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.street_address}, {self.city}, {self.state}, {self.country}"