from django.contrib.auth import get_user_model
from .models import Customer, Vendor, CustomerAddress, VendorAddress
from rest_framework import serializers
from django.db import transaction
import re

User = get_user_model()



class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields =['email', 'password', 'role', 'is_verified']
        extra_kwargs = {'password': {'write_only': True, 'required': False},
                        'email':{'validators':[]}}

    def validate_email(self, value):
        email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

        if not re.match(email_pattern, value):
            raise serializers.ValidationError("Please enter a valid email address.")
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
    email = serializers.EmailField(write_only = True, required = False)
    password = serializers.CharField(write_only = True, required = False)

    class Meta:
        model = Customer
        fields = ['user','email', 'password', 'first_name', 'last_name', 'phone_number','profile_picture']
        extra_kwargs = {
            'phone_number': {'validators': []},
        }

    def validate_phone_number(self,value):
        instance = self.instance
        if instance:
            if instance.phone_number == value:
                return value

            if Customer.objects.filter(phone_number = value).exclude(pk = instance.pk).exists():
                raise serializers.ValidationError("This phone number is already in use")
        else:
            if Customer.objects.filter(phone_number = value).exists():
                raise serializers.ValidationError('This phone number is already in use.')
        return value
    def create(self, validated_data):
        email = validated_data.pop('email')
        password = validated_data.pop('password')
        user_data = {'email': email, 'password': password, 'role': 'customer'}
        user_serializer = CustomUserSerializer(data= user_data)
        user_serializer.is_valid(raise_exception = True)
        user = user_serializer.save()

        customer = Customer.objects.create(user = user, **validated_data)
        return customer
    
    def update(self, instance, validated_data):
        user = instance.user
        with transaction.atomic():
            email = validated_data.pop('email', None)
            password = validated_data.pop('password', None)

            if email and email != user.email:
                if User.objects.filter(email=email).exclude(id=user.id).exists():
                    raise serializers.ValidationError({"email": "This email is already in use."})
                user.email = email


            instance.first_name = validated_data.get('first_name', instance.first_name)
            instance.last_name = validated_data.get('last_name', instance.last_name)
            instance.phone_number = validated_data.get('phone_number', instance.phone_number)
            instance.profile_picture = validated_data.get('profile_picture', instance.profile_picture)
            instance.save()

        return instance


class VendorAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorAddress
        fields = ['vendor','street_address', 'city', 'state', 'country', 'pincode']
    
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
    pincode = serializers.CharField()

    class Meta:
        model = Vendor
        fields = ['user','email','password', 'first_name', 'last_name', 'phone_number', 'company_name', 'street_address', 'city', 'state', 'country', 'pincode','profile_picture']

    

    def validate_phone_number(self,value):
        instance = self.instance
        if instance:
            if instance.phone_number == value:
                return value
        

            if Vendor.objects.filter(phone_number = value).exclude(pk = instance.id if instance else None).exists():
                raise serializers.ValidationError("This phone number is already in use")
        else:
            if Customer.objects.filter(phone_number = value).exists():
                raise serializers.ValidationError('This phone number is already in use.')
        return value
        
    
    def validate_company_name(self, value):
        instance = self.instance

        if instance:
            if instance.company_name == value:
                return value
        
            if Vendor.objects.filter(company_name = value).exclude(pk = instance.id if instance else None).exists():
                raise serializers.ValidationError("This company already holds an account.")
        else:
            if Vendor.objects.filter(company_name = value).exists():
                raise serializers.ValidationError('This company already exists.')
        return value

    def create(self, validated_data):   
        email = validated_data.pop('email')
        password = validated_data.pop('password')
        user_data = {'email': email, 'password': password, 'role': 'vendor', 'is_verified': False}

        street_address = validated_data.pop('street_address')
        city = validated_data.pop('city')
        state = validated_data.pop('state')
        country = validated_data.pop('country')
        pincode = validated_data.pop('pincode')

        with transaction.atomic():

            user_serializer = CustomUserSerializer(data = user_data)
            user_serializer.is_valid(raise_exception=True) 
            user = user_serializer.save()
            vendor = Vendor.objects.create(user = user, **validated_data)

            address_data = {'vendor': vendor.id, 'street_address': street_address, 'city': city, 'state': state, 'country': country, 'pincode': pincode}
            vendor_address = VendorAddressSerializer(data = address_data)
            vendor_address.is_valid(raise_exception = True)
            vendor_address.save()   

        return vendor
    
    def update(self,instance,validated_data):
        user = instance.user

        with transaction.atomic():
            email = validated_data.pop('email', None)

            if email and email != user.email:
                if User.objects.filter(email = email).exclude(id =user.id).exists():
                    raise serializers.ValidationError({"email":"This email already exists"}) 
                user.email = email
            user.save()

            instance.first_name =validated_data.get('first_name',instance.first_name)
            instance.last_name = validated_data.get('last_name',instance.last_name)
            instance.phone_number = validated_data.get('phone_number',instance.phone_number)
            instance.company_name = validated_data.get('company_name',  instance.company_name)
            instance.profile_picture = validated_data.get('profile_picture', instance.profile_picture)
            instance.save()

            vendor_address = instance.vendor_address


            vendor_address.street_address = validated_data.get('street_address', vendor_address.street_address)
            vendor_address.city = validated_data.get('city',vendor_address.city)
            vendor_address.state = validated_data.get('state',vendor_address.state)
            vendor_address.country = validated_data.get('country', vendor_address.country)
            vendor_address.pincode = validated_data.get('pincode', vendor_address.pincode)
            vendor_address.save()

        return instance


       
           
