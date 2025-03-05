import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ProductSerializer
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view,permission_classes
from authentication.models import Vendor
from admin_side.views import CustomPagination
from authentication.serializers import VendorSerializer
from .models import Products
from authentication.permissions import IsAuthenticatedAndNotBlocked, IsVendor   
from cart_and_orders.models import OrderItems
from vendor_side.models import ProductVariants
from django.shortcuts import get_object_or_404
# Create your views here.

class Product_create_view(APIView):
    parser_classes = (MultiPartParser, FormParser)
    def post(self, request):
        print(request.user)
        print(request.COOKIES)
        if not request.user.is_authenticated or request.user.role != 'vendor':
            return Response({"error": "Only vendors can create products"}, status = status.HTTP_403_FORBIDDEN)
        
        variants_data = request.data.get('variants',[])
        variants_parsed_data = []
        if isinstance(variants_data, str):
            try:
                variants_parsed_data = json.loads(variants_data)
            except json.JSONDecodeError:
                return Response({'error':'Invalid variants data. Expected a JSON array.'},status=status.HTTP_400_BAD_REQUEST)
        
        
        if not variants_parsed_data:
            return Response({'error': 'At least one variant should be defined.'}, status=status.HTTP_400_BAD_REQUEST)
        
        image_list = request.FILES.getlist('images')
        print(image_list)
        if len(image_list) < 3:
            return Response({"error":"At least 3 images are required"}, status=status.HTTP_400_BAD_REQUEST)

        images_data = [{'image':image} for image in image_list] 
        print("Variants data:",variants_data)
        print('images_data_in_view: ', images_data)
        product_data = {
            'name': request.data.get('name'),
            'category': request.data.get('category'),
            'description': request.data.get('description'),
            'images': images_data,
            'variants':variants_parsed_data
        }
        print("product_data: ",product_data)
        serializer = ProductSerializer(data = product_data, context = {'request':request})
        if serializer.is_valid():
            product = serializer.save()
            return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
def product_listing_vendor(request):   #This get method is used to call all not deleted product details on vendor side and customer side.
    user = request.user
    print("vendor_side_product_listing debug: ",user)

    if not user.is_authenticated or user.is_blocked and user.role == 'vendor':
        return Response({'error': 'The vendor is not authenticated.'}, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        vendor = user.vendor_profile
    except Vendor.DoesNotExist:
        return Response({'error': 'Vendor not found'}, status=status.HTTP_404_NOT_FOUND)
    
    products = vendor.vendor_products.filter(is_deleted = False)
    
    product_data = []
    
    for product in products:
        product_image_instance = product.product_images.first()
        image_url = request.build_absolute_uri(product_image_instance.image.url)
        variants = product.variant_profile.filter(is_deleted = False)
        variant_data = []
        for variant in variants:
            if not variant.variant_unit == 'packet of':
                variant_name = f'{variant.quantity} {variant.variant_unit}'
            else:
                variant_name = f'{variant.variant_unit} {variant.quantity}'
            variant_data.append({
                'id': variant.id,
                'name': variant_name,
                'price': variant.price,
                'stock': variant.stock
            })
        product_data.append({
            'id':product.id,
            'product_name':product.name,
            'product_image':image_url,
            'category': product.category.category,
            'variants': variant_data
        })


    paginator = CustomPagination()
    paginated_products = paginator.paginate_queryset(product_data, request)

    if paginated_products is not None:
        return paginator.get_paginated_response(paginated_products)
    return Response([])


@api_view(['PATCH'])
def vendor_profile_update(request):
    user = request.user
    if not user.is_authenticated or user.is_blocked or not user.is_verified:
        return Response({"error":"Vendor is not found"},status=status.HTTP_404_NOT_FOUND)
    
    vendor_instance = user.vendor_profile
    data = request.data.copy()

    if 'profile_picture' not in data:
        data.pop('profile_picture',None)
    
    serializer = VendorSerializer(instance = vendor_instance, data = data, partial = True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    response = Response({
        'role': user.role,
        'first_name': user.vendor_profile.first_name,
        'last_name': user.vendor_profile.last_name,
        'email': user.email,
        'phone_number':user.vendor_profile.phone_number,
        'profile_picture': request.build_absolute_uri(user.vendor_profile.profile_picture.url) if user.vendor_profile.profile_picture else None,
        'company_name': user.vendor_profile.company_name,
        'street_address':user.vendor_profile.vendor_address.street_address,
        'city': user.vendor_profile.vendor_address.city,
        'country': user.vendor_profile.vendor_address.country,
        'state': user.vendor_profile.vendor_address.state,
        'pincode': user.vendor_profile.vendor_address.pincode,
    },status=status.HTTP_200_OK)

    return response


class ProductDetailsEdit(APIView):
    def get(self,request,product_id):  #this is used to fetch the product details when the vendor is editing the product and also when the user is requesting profile details.
        user= request.user

        if user and user.is_authenticated and not user.is_blocked:
            try:
                product = Products.objects.select_related('vendor', 'category').prefetch_related('variant_profile','product_images').get(id=product_id)

                product_data = {
                    'id': product.id,
                    'name': product.name,
                    'description': product.description,
                    'category': product.category.category,
                    'variants':[
                        {
                            'id':variant.id,
                            'quantity':variant.quantity,
                            'variant_unit':variant.variant_unit,
                            'price':variant.price,
                            'stock':variant.stock,
                            'is_out_of_stock': variant.stock == 0,
                        }
                        for variant in product.variant_profile.filter(is_deleted = False)
                    ],
                    'images':[
                        {
                            'id':img.id,
                            'url':request.build_absolute_uri(img.image.url)
                        }
                        for img in product.product_images.all()
                    ]
                }

                return Response(product_data, status = status.HTTP_200_OK)
            
            except Products.DoesNotExist:
                return Response({"error":"Product not found."},status=status.HTTP_404_NOT_FOUND)
    

    def put(self, request, product_id):
        user = request.user

        if user.is_authenticated and not user.is_blocked and user.role == 'vendor':
            variants = request.data.get('variants', [])
            variants_parsed_data = []
            if isinstance(variants, str):
                try:
                    variants_parsed_data = json.loads(variants)
                except json.JSONDecodeError:
                    return Response({'error':'Invalid variants data.Expected JSON array.'},status=status.HTTP_400_BAD_REQUEST)
                
            
            if not variants_parsed_data:
                return Response({'error':'Atleast one variant should be present'},status=status.HTTP_400_BAD_REQUEST)
            
            image_list =request.FILES.getlist('images')

            productinstance = Products.objects.get(pk = product_id)

            images_to_be_deleted = request.data.get('images_to_delete',[])
            images_to_be_deleted_parsed = []
            if isinstance(images_to_be_deleted, str):
                try:
                    images_to_be_deleted_parsed = json.loads(images_to_be_deleted)
                except json.JSONDecodeError:
                    return Response({'error':'Invalid data received in delete image id'},status=status.HTTP_400_BAD_REQUEST)
            
            print(images_to_be_deleted_parsed)
            number_of_images_to_delete = len(images_to_be_deleted_parsed)

            length_of_image_list = len(image_list)

            product_images_present = len(productinstance.product_images.all())

            if product_images_present + length_of_image_list-number_of_images_to_delete < 3:
                return Response({'error':'The product images cannot go below 3.'},status=status.HTTP_400_BAD_REQUEST)
            
            for image_id in images_to_be_deleted_parsed:
                productinstance.product_images.filter(pk =image_id).delete()
                
            if length_of_image_list == 0:
                image_data = [{'id': img.id, 'image': img.image} for img in productinstance.product_images.all()]
            else:
                image_data = [{'image': image} for image in image_list] 
            product_data_update = {
                'name': request.data.get('name'),
                'description': request.data.get('description'),
                'category': request.data.get('category'),
                'images': image_data,
                'variants':variants_parsed_data
            }
            print(product_data_update)

            serializer = ProductSerializer(productinstance, data = product_data_update, context = {'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status = status.HTTP_200_OK)
            return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)
        
    def delete(self, request, product_id):
        user = request.user

        if user.is_authenticated and not user.is_blocked:
            try:
                product = Products.objects.get(id = product_id)
                product.is_deleted = True
                product.save()
            except Products.DoesNotExist:
                return Response({'error':'The product does not exist'},status=status.HTTP_400_BAD_REQUEST) 


        return Response({'message':'Success'},status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsVendor, IsAuthenticatedAndNotBlocked])
def vendor_order(request):
    vendor= request.user.vendor_profile
    order_items =  OrderItems.objects.filter(
        variant__product__vendor = vendor
    ).select_related(
        'order',
        'variant__product'
    ).prefetch_related(
        'variant__product__product_images',
        'order__order_shipping_address'
    )

    response_data_orders = []
    for item in order_items:
            shipping_address = item.order.order_shipping_address.first()
            product_image = item.variant.product.product_images.first()
            image_url = request.build_absolute_uri(product_image.image.url) if product_image else None
            response_data_order = {
                'order_item_id':item.id,
                'quantity': item.quantity,
                'price': item.price,
                'status':item.get_order_item_status_display(),
                'created_at': item.order.created_at.strftime("%Y-%m-%d %H:%M"),
                'image_url': image_url,
                'shipping_address':{
                    'name': shipping_address.name,
                    'phone_number': shipping_address.phone_number,
                    'street_address': shipping_address.street_address,
                    'city': shipping_address.city,
                    'state': shipping_address.state,
                    'country': shipping_address.country,
                    'pincode':shipping_address.pincode,
                }
            }
            response_data_orders.append(response_data_order)
    
    return Response(response_data_orders, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsVendor, IsAuthenticatedAndNotBlocked])
def vendor_order_status_update(request, order_item_id):
    vendor = request.user.vendor_profile
    order_status = request.data.get('status', '').lower()



    if order_status not in ['dispatched', 'cancelled']:
        return Response({'error':'The order status cannot be changed back to processing.'},status=status.HTTP_400_BAD_REQUEST)

    try:
        cancel_reason = request.data.get('cancellation_reason', '')
        order_item = get_object_or_404(OrderItems, id = order_item_id)
        if order_item.variant.product.vendor.id != vendor.id:
            return Response({'error': 'Vendor not authorized'}, status=status.HTTP_403_FORBIDDEN)
        
        if order_item.order_item_status == 'processing' and order_status =='dispatched':
            print('are we inside this function')
            order_item.order_item_status = order_status
            order_item.save()
            return Response({'message': 'status updated successfully'}, status=status.HTTP_200_OK)
        elif order_item.order_item_status == 'processing' and order_status == 'cancelled':
            order_item.order_item_status = order_status
            order_item.cancel_reason = f"{cancel_reason} cancelled by {vendor.first_name}"
            order_item.save()
            return Response({'message': 'status and reason updated successfully'}, status=status.HTTP_200_OK)
        elif order_item.order_item_status == 'dispatched':
            return Response({'message':'The order has already been dispatched and can only be returned or cancelled by the admin. You can raise a concern if you like.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error':'Invalid status transition'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(str(e))
        return Response({'error':'An Internal server error occured'}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)

        
        