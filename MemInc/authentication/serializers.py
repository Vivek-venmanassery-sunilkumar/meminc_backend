from django.contrib.auth import get_user_model
from .models import Customer, Vendor, CustomerAddress, VendorAddress
from rest_framework import serializers

User = get_user_model()

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields =['id', 'email', 'password', 'role']

class CustomerSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()

    class Meta:
        model = Customer
        fields = ['user', 'first_name', 'last_name', 'phone_number']

    def create(self, validated_data):
        email = validated_data.pop('email')
        password = validated_data.pop('password')

        user = User.objects.create_user(email = email, password = password, role = 'customer')

        customer = Customer.objects.create(user = user, **validated_data)
        return customer