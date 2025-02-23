import re
from rest_framework import serializers
from authentication.models import Vendor
from .models import Products,ProductVariants,Categories,ProductImages
from django.db import transaction
from django.core.exceptions import ValidationError 
        

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Categories
        fields = ['id','category','is_enabled']
    
    def validate_category(self, value):
        if Categories.objects.filter(category__iexact = value.lower()).exists():
            raise serializers.ValidationError({"error":"This category already exists."})
        return value

class VariantsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariants
        fields = ['quantity', 'price','stock','variant_unit']
    
    def validate_quantity(self, value):
        if value<=0:
            raise serializers.ValidationError("Quantity must be greater than 0")
        return value
    
    def validate_stock(self, value):
        if value <=0:
            raise serializers.ValidationError("Stock must be greater than 0")
        return value
    
    def validate_price(self, value):
        if value<=0:
            raise serializers.ValidationError("Price must be greater than 0")
        return value

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImages
        fields = ['image']
    
    def validate_image(self, value):
        valid_mime_types = ['image/jpeg', 'image/png', 'image/webp']

        if value.content_type not in valid_mime_types:
            raise serializers.ValidationError("Only JPEG, PNG and WebP formats are allowed")
        
        max_size = 5*1024*1024

        if value.size > max_size:
            raise serializers.ValidationError("Image size should not exceed 5MB.")
        
        return value

class ProductSerializer(serializers.ModelSerializer):
    category = serializers.CharField(write_only = True)
    images = ProductImageSerializer(many = True, write_only = True)
    variants = VariantsSerializer(many = True, write_only = True)
    class Meta:
        model = Products
        fields = ['name','category','description', 'images', 'variants']

    def validate_description(self, value):
        min_length = 50
        max_length = 1000

        if len(value) < min_length:
            raise serializers.ValidationError(f"Description must be at lease {min_length} characters long.")

        if len(value)>max_length:
            raise serializers.ValidationError(f"Description must be less than {max_length} characters long.")
        
        if re.search(r"(https?://|www\.)",value) or re.search(r"[a-zA-Z0-9,_%+-]+@[a-zA-Z]{2,}",value):
            raise serializers.ValidationError(f"Description cannot conatain links or email addresses")
        
        if not re.search(r"[A-Za-z0-9,;'\'\-\(\)]+[.!?]", value):
            raise serializers.ValidationError("Descripton must be in complete sentences.")
        
        return value

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get('request')
        
        if not request or not request.user:
            raise serializers.ValidationError('Authentication required') 
        
        try:
            vendor = request.user.vendor_profile
        except Vendor.DoesNotExist:
           raise serializers.ValidationError("You have no authority")
        
        category_name  = validated_data.pop('category')
       
        try:
            category = Categories.objects.get(category__iexact = category_name.lower())
        except Categories.DoesNotExist:
            raise ValidationError({'error':'Category does not exist.'})                 
        variant_data_array = validated_data.pop('variants')
       
        image_data_array = validated_data.pop('images')

        product = Products.objects.create(category = category, vendor = vendor, **validated_data)

        for variant in variant_data_array:

            variant_serializer = VariantsSerializer(data = variant)
            if variant_serializer.is_valid():
                variant_serializer.save(product = product)
            else:
                raise serializers.ValidationError(variant_serializer.errors)
        

        for image in image_data_array:
            image_serializer = ProductImageSerializer(data = image)
            if image_serializer.is_valid():
               
                image_serializer.save(product = product)
            else:
                raise serializers.ValidationError(image_serializer.errors)
        
        return product
    
    @transaction.atomic()
    def update(self, instance, validated_data):
        request = self.context.get('request')

        if not request or not request.user:
            raise serializers.ValidationError('Authentication required')
        
        try:
            vendor = request.user.vendor_profile
        except Vendor.DoesNotExist:
            raise serializers.ValidationError('You have no authority')
        
        category_name = validated_data.pop('category')
        try:
            category = Categories.objects.get(category__iexact = category_name.lower())
            instance.category = category
        except Categories.DoesNotExist:
            raise serializers.ValidationError({"error":"Category does not exist."})
         

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        
        variant_data_array = validated_data.pop('variants',[])
        existing_variants = instance.variant_profile.all()

        existing_variant_ids = {variant.id for variant in existing_variants}

        incoming_variant_ids = {variant.get('id') for variant in variant_data_array if isinstance(variant.get('id'), int)}

        for existing_variant in existing_variants:
            if existing_variant.id not in incoming_variant_ids:
                existing_variant.is_deleted = True
                existing_variant.save()

        for variant in variant_data_array:
            variant_id = variant.get('id')

            if isinstance(variant_id, int) and variant_id in existing_variant_ids:
                existing_variant = instance.variant_profile.get(id = variant_id)
                variant_serializer = VariantsSerializer(existing_variant, data = variant, partial = True)
            else:
                variant_serializer = VariantsSerializer(data = variant)
            
            if variant_serializer.is_valid():
                variant_serializer.save(product = instance)
            else:
                raise serializers.ValidationError(variant_serializer.errors)



        if 'images' in validated_data:
            image_data_array = validated_data.pop('images')
            instance.product_images.all().delete()

            for image in image_data_array:
                image_serializer = ProductImageSerializer(data = image)
                if image_serializer.is_valid():
                    image_serializer.save(product = instance)
                else:
                    raise serializers.ValidationError(image_serializer.errors)
        return instance




            
        



    
