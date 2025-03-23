import re
from rest_framework import serializers
from authentication.models import Vendor
from .models import Products,ProductVariants,Categories,ProductImages
from django.db import transaction
from django.core.exceptions import ValidationError 
from django.utils.timezone import now
from datetime import timedelta
from cart_and_orders.models import OrderItems
from django.db.models import Sum
        

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




class VendorDashboard(serializers.Serializer):
    total_sales = serializers.DecimalField(max_digits=10, decimal_places=2, read_only = True) 
    payout_recieved = serializers.DecimalField(max_digits=10, decimal_places=2, read_only = True)
    payout_pending = serializers.IntegerField(read_only = True)
    total_orders_recieved = serializers.IntegerField(read_only = True)
    completed_orders = serializers.IntegerField(read_only = True)
    cancelled_orders = serializers.IntegerField(read_only = True)
    pending_orders = serializers.IntegerField(read_only = True)
    top_selling_product = serializers.CharField(max_length = 150, read_only = True)
    company_name = serializers.CharField(max_length = 100, read_only = True)
    

    def to_representation(self, instance):
        request = self.context.get('request')
        filter_type = request.query_params.get('filter', 'daily')    
        end_date = now()
        vendor = request.user.vendor_profile
        if filter_type == 'daily':
            start_date = end_date - timedelta(days=1)
        elif filter_type == 'weekly':
            start_date = end_date - timedelta(weeks = 1)
        elif filter_type == 'monthly':
            start_date = end_date - timedelta(days = 30)
        else:
            start_date = end_date - timedelta(days = 1)

        total_sales = OrderItems.objects.filter(order_item_status = 'delivered', created_at__range = (start_date, end_date), variant__product__vendor = vendor).aggregate(total_revenue_generated = Sum('price'))['total_revenue_generated'] or 0
        payout_recieved = OrderItems.objects.filter(is_payment_done_to_vendor = True, created_at__range = (start_date, end_date), variant__product__vendor = vendor).aggregate(total_payment_received = Sum('payment_done_to_vendor'))['total_payment_received'] or 0
        payout_pending = OrderItems.objects.filter(order_item_status = 'delivered', is_payment_done_to_vendor = False, created_at__range=(start_date, end_date), variant__product__vendor = vendor).count() or 0
        total_orders_recieved = OrderItems.objects.filter(created_at__range = (start_date, end_date), variant__product__vendor = vendor).count() or 0
        completed_orders = OrderItems.objects.filter(created_at__range = (start_date, end_date), variant__product__vendor = vendor, order_item_status = 'delivered').count() or 0
        cancelled_orders = OrderItems.objects.filter(created_at__range = (start_date, end_date), variant__product__vendor = vendor, order_item_status = 'cancelled').count() or 0
        pending_orders = OrderItems.objects.exclude(order_item_status__in = ['delivered', 'cancelled']).filter(created_at__range = (start_date, end_date), variant__product__vendor = vendor).count() or 0
        top_selling_product = OrderItems.objects.filter(created_at__range = (start_date, end_date), order_item_status = 'delivered', variant__product__vendor = vendor).values('variant__product__name').annotate(total = Sum('quantity')).order_by('-total').first()
        company_name = vendor.company_name
    

        product_name =  top_selling_product['variant__product__name'] if top_selling_product else "no sales data"

        data = {
            'company_name': company_name,
            'total_sales': total_sales,
            'payout_recieved': payout_recieved,
            'payout_pending': payout_pending,
            'total_order_recieved': total_orders_recieved,
            'completed_orders': completed_orders,
            'cancelled_orders': cancelled_orders,
            'pending_orders': pending_orders,
            'top_selling_product': product_name
        }

        return data