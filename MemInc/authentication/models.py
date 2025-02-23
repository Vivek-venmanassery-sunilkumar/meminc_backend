from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
import os



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
        extra_fields.setdefault('is_staff', True)

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
    is_verified = models.BooleanField(default = True)
    is_staff = models.BooleanField(default= False)


    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

class Customer(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name = 'customer_profile')
    first_name = models.CharField(max_length = 100)
    last_name = models.CharField(max_length= 100)
    phone_number = models.CharField(max_length=13, unique=True, null = True, blank=True)  
    profile_picture = models.ImageField(upload_to='profile_pictures/customers/', null=True, blank=True)
    profile_picture_url = models.URLField(blank = True)

    def save(self, *args, **kwargs):
        if not self.user.is_blocked:
            self.user.is_active = True
        else:
            self.user.is_active = False
        self.user.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    

    
class CustomerAddress(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name = 'customer_addresses')
    street_address = models.CharField(max_length=100, blank = False, null=False)
    city = models.CharField(max_length=100, blank=False, null=False)
    state = models.CharField(max_length=100, blank=False, null=False)
    country = models.CharField(max_length=100, blank=False, null=False)
    pincode = models.CharField(max_length=20, blank=False, null=False)

    def __str__(self):
        return f"{self.street_address}, {self.city}, {self.state}, {self.country}"


    
class Vendor(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='vendor_profile')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    company_name = models.CharField(max_length=200, unique=True)
    phone_number = models.CharField(max_length=15)
    profile_picture = models.ImageField(upload_to='profile_pictures/vendors/', null=True, blank=True)
    
    def save(self, *args, **kwargs):

        self.user.save()
        super().save(*args, **kwargs)

class VendorAddress(models.Model):
    vendor = models.OneToOneField(Vendor, on_delete = models.CASCADE, related_name = 'vendor_address')
    street_address = models.CharField(max_length = 100)
    city = models.CharField(max_length = 100)
    state = models.CharField(max_length = 100)
    country = models.CharField(max_length = 100)
    pincode = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.street_address}, {self.city}, {self.state}, {self.country}"