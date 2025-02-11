from rest_framework import serializers
from authentication.models import Vendor
from .models import Products,Product_variants,Categories
from django.db import transaction



class categories_serializer(serializers.ModelSerializer):
    class Meta:
        model = Categories
        fields = ['category']


class variants_serializer(serializers.ModelSerializer):
    class Meta:
        model = Product_variants
        fields = ['product_id', 'quantity', 'price','stock']
    
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


class product_serializer(serializers.ModelSerializer):
    category_id = serializers.PrimaryKeyRelatedField(source = 'category',read_only = True)
    category = serializers.CharField(write_only = True)
    variants = variants_serializer(many=True,write_only=True)
    vendor = serializers.PrimaryKeyRelatedField()

    class Meta:
        model = Products
        fields = ['category_id','category','name','description','image','variantunit','variants','vendor']

    def validate_variants(self,value):
        if not value:
            raise serializers.ValidationError("At least one variant is required")
        return value
    

    @transaction.atomic
    def create(self, validated_data):
        category_name = validated_data.pop('category')
        category, created = Categories.objects.get_or_create(
            category_iexact = category_name.lower(),
            defaults = {'category': category_name.lower()}
        )
        variant_data_array = validated_data.pop('variants')

        product = Products.objects.create(category = category, **validated_data)
    
        for variant_data in variant_data_array:
            variant_serializer = variants_serializer(data = variant_data)
            variant_serializer.is_valid(raise_exception=True)
            variant_serializer.save(product = product)
        
        return product

        





    
