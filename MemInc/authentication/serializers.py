from django.contrib.auth import get_user_model
from .models import Customer, Vendor, CustomerAddress, VendorAddress
from rest_framework import serializers
from django.db import transaction

User = get_user_model()

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields =['email', 'password', 'role']
        extra_kwargs = {'password': {'write_only': True}}

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already in Use. Please try another one.")
        return value
    
    def validate_password(self, value):
        if len(value)<8:
            raise serializers.ValidationError("The password must contain atleast 8 characters")
        return value
    
    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class CustomerSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only = True)
    email = serializers.EmailField(write_only = True)
    password = serializers.CharField(write_only = True)

    class Meta:
        model = Customer
        fields = ['user','email', 'password', 'first_name', 'last_name', 'phone_number']

    def create(self, validated_data):
        email = validated_data.pop('email')
        password = validated_data.pop('password')
        user_data = {'email': email, 'password': password, 'role': 'customer'}
        user_serializer = CustomUserSerializer(data= user_data)
        user_serializer.is_valid(raise_exception = True)
        user = user_serializer.save()

        customer = Customer.objects.create(user = user, **validated_data)
        return customer


class VendorAddressSerializer(serializers.ModelSerializer):
    vendor = serializers.PrimaryKeyRelatedField(read_only = True)
    class Meta:
        model = VendorAddress
        fields = ['street_address', 'city', 'state', 'country', 'pincode']
    
    def validate_pincode(self,value):
        if len(value) != 6:
            raise serializers.ValidationError('The pincode is not valid')
        return value


class VendorSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only = True)
    email = serializers.EmailField()
    password = serializers.CharField(write_only = True)
    street_address = serializers.CharField()
    city = serializers.CharField()
    state = serializers.CharField()
    country = serializers.CharField()
    pincode = serializers.IntegerField()

    class Meta:
        model = Vendor
        fields = ['email','password', 'first_name', 'last_name', 'phone_number', 'company_name', 'street_address', 'city', 'state', 'country', 'pincode']

    def create(self, validated_data):   
        email = validated_data.pop('email')
        password = validated_data.pop('password')
        user_data = {'email': email, 'password': password, 'role': 'vendor'}

        street_address = validated_data.pop('street_address')
        city = validated_data.pop('city')
        state = validated_data.pop('state')
        country = validated_data.pop('country')
        pincode = validated_data.pop('pincode')
        address_data = {'street_address': street_address, 'city': city, 'state': state, 'country': country, 'pincode': pincode}

        with transaction.atomic():

            user_serializer = CustomUserSerializer(data = user_data)
            user_serializer.is_valid(raise_exception=True) 
            user = user_serializer.save()
            vendor = Vendor.objects.create(user = user, **validated_data)

            address_data['vendor'] = vendor.id

            vendor_address = VendorAddressSerializer(data = address_data)
            vendor_address.is_valid(raise_exception = True)
            vendor_address.save()   

        return vendor