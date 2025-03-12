from rest_framework.response import Response
from rest_framework import status
from vendor_side.models import Products
from rest_framework.decorators import api_view, permission_classes
from admin_side.views import CustomPagination
from authentication.serializers import CustomerSerializer
from .serializers import CustomerAddressSerializer
from rest_framework.views import APIView
from authentication.permissions import IsAuthenticatedAndNotBlocked,IsCustomer
from authentication.models import CustomerAddress
from admin_side.models import Coupon, UsedCoupon
from decimal import Decimal
# Create your views here.


@api_view(['GET'])
def product_listing_customer_side(request):
    products = Products.objects.all()

    product_data = []
    for product in products:
        if product.is_deleted == False:
            image_url = request.build_absolute_uri(product.product_images.first().image.url) 
            variants = product.variant_profile.all()
            variant_data = []
            for variant in variants:
                if variant.is_deleted == False:
                    variant_data.append({
                        'id': variant.id,
                        'name': f'{variant.quantity} {variant.variant_unit}',
                        'price': variant.price,
                        'stock': variant.stock,
                        'is_out_of_stock': variant.stock == 0,
                    })
            product_data.append({
                'id':product.id,
                'product_name':product.name,
                'product_image':image_url,
                'category': product.category.category,
                'company_name': product.vendor.company_name,
                'variants': variant_data
            })


    paginator = CustomPagination()
    paginated_products = paginator.paginate_queryset(product_data, request)

    if paginated_products is not None:
        return paginator.get_paginated_response(paginated_products)
    return Response([])


@api_view(['PATCH'])
def customer_profile_update(request):
    user = request.user
    if not user.is_authenticated or user.is_blocked:
        return Response({"error":"Customer is not found"}, status=status.HTTP_404_NOT_FOUND)
    
    customer_instance = user.customer_profile
    data = request.data.copy()
    if 'profile_picture' not in data:
        data.pop('profile_picture', None)

    serializer = CustomerSerializer(instance = customer_instance, data = data, partial = True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    response = Response({
         'role': user.role,
         'first_name': user.customer_profile.first_name,
         'last_name': user.customer_profile.last_name,
         'email': user.email,
         'phone_number': user.customer_profile.phone_number,
         'profile_picture': request.build_absolute_uri(user.customer_profile.profile_picture.url) if user.customer_profile.profile_picture else None,
    },status=status.HTTP_200_OK)
    return response
    
    
# view functions for the crud operations on customer addresses    

class AddressManagementCustomer(APIView):
    
    permission_classes = [IsAuthenticatedAndNotBlocked]
    def post(self, request):
        address_data = request.data

        customer = request.user.customer_profile
        address_serializer = CustomerAddressSerializer(data= address_data)

        if not address_serializer.is_valid():
            return Response(address_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        address_serializer.save(customer = customer)

        return Response(address_serializer.data,status=status.HTTP_201_CREATED)
    

    def get(self, request, address_id = None):
        if address_id is not None:
            try:
                address_data = CustomerAddress.objects.get(id = address_id, customer= request.user.customer_profile)
                serializer = CustomerAddressSerializer(address_data)
                return Response(serializer.data, status = status.HTTP_200_OK)
            except CustomerAddress.DoesNotExist:
                return Response({'message':'Address does not exist'}, status=status.HTTP_404_NOT_FOUND)
        
        else:
            address_data = CustomerAddress.objects.filter(customer = request.user.customer_profile)
            serializer = CustomerAddressSerializer(address_data, many= True)
            return Response(serializer.data, status=status.HTTP_200_OK) 
        

    def put(self, request, address_id):
        try:
            address_data = CustomerAddress.objects.get(id = address_id, customer = request.user.customer_profile)
            serializer = CustomerAddressSerializer(address_data, data=request.data, partial = True)

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except CustomerAddress.DoesNotExist:
            return Response({"error":"Address not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error":str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def delete(self, request, address_id):
        try:
            address_data = CustomerAddress.objects.get(id = address_id, customer = request.user.customer_profile)
            address_data.delete()
            return Response({'message': 'Address deleted successfully'}, status=status.HTTP_200_OK)
        except CustomerAddress.DoesNotExist:
            return Response({'error':'Address not found'}, status=status.HTTP_404_NOT_FOUND)
        



@api_view(['GET'])
@permission_classes([IsCustomer])
def customer_coupons(request):
    try:
        total_price = request.GET.get('total_price')
        coupons = Coupon.objects.filter(is_active = True, is_active_admin = True)
        used_coupon_instance = UsedCoupon.objects.filter(user = request.user)
        used_coupons = []
        for used_coupon in used_coupon_instance:
            used_coupons.append(used_coupon.coupon)
        response= []
        for coupon in coupons:
            if coupon not in used_coupons:
                if Decimal(total_price) >= coupon.min_order_value:
                    response_coupon = {
                        'id': coupon.id,
                        'code': coupon.code,
                        'coupon_type': coupon.discount_type,
                        'discount_value': coupon.discount_value,
                        'max_discount': coupon.max_discount,
                        'min_order_value': coupon.min_order_value,
                    }
                    response.append(response_coupon)
        
        return Response(response, status=status.HTTP_200_OK)
    except Coupon.DoesNotExist:
        return Response({'message':'No available coupons'}, status=status.HTTP_400_BAD_REQUEST)
