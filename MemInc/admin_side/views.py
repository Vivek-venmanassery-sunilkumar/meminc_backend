from rest_framework.decorators import api_view, permission_classes
from .serializers import AdminDashboard
from django.db.models import Q
from datetime import timedelta
from authentication.permissions import IsAuthenticatedAndNotBlocked
from cart_and_orders.models import OrderItems, Payments
from rest_framework.views import APIView
from authentication.models import Customer, Vendor
from rest_framework.pagination import PageNumberPagination 
from rest_framework.response import Response
from rest_framework import status
import math
from django.contrib.auth import get_user_model
from vendor_side.models import Categories
from vendor_side.serializers import CategorySerializer
from authentication.permissions import IsAdmin, IsCustomer
from .serializers import CouponSerializer, AdminDashboard, BannerSerializer
from .models import Coupon, Banner
from wallet.models import Wallet, WalletTransactionsAdmin
from django.db import transaction
from django.utils import timezone
from django.utils.timezone import now
from vendor_side.models import Products

User = get_user_model()

class CustomPagination(PageNumberPagination):
    page_size = 10

    def get_paginated_response(self, data):
        total_pages = math.ceil(self.page.paginator.count/self.page_size)
        return Response({
            'count':self.page.paginator.count,
            'total_pages': total_pages,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })

@api_view(['GET'])
def list_customer(request):
    search_query = request.GET.get('search', '').strip()

    customers =Customer.objects.select_related('user').values('first_name', 'last_name', 'phone_number', 'user__id', 'user__is_blocked', 'user__email')

    if search_query:
        customers = customers.filter(Q(first_name__icontains = search_query) | Q(last_name__icontains = search_query) | Q(user__email__icontains =search_query))
    paginator = CustomPagination()
    paginated_customers =  paginator.paginate_queryset(customers, request)
    
    if paginated_customers is not None:
        return paginator.get_paginated_response(paginated_customers)    
    return Response([])

@api_view(['GET'])
def list_vendor(request):
    search_query = request.GET.get('search', '').strip()
    vendors = Vendor.objects.select_related('user').values('first_name', 'last_name', 'phone_number', 'user__id', 'user__is_blocked','user__email','user__is_verified','company_name')

    if search_query:
        vendors = vendors.filter(Q(first_name__icontains = search_query) | Q(last_name__icontains = search_query) | Q(user__email__icontains = search_query))
    paginator = CustomPagination()
    paginated_vendors = paginator.paginate_queryset(vendors, request)

    if paginated_vendors is not None:
        return paginator.get_paginated_response(paginated_vendors)
    return Response([])

@api_view(['PUT'])
def block_user(request):
    access_token = request.COOKIES.get('access_token')
    print(access_token)
    user = User.objects.filter(id=3).first()
    print(user)
    user_id = request.GET.get('id')

    if not user_id:
        return Response({'error': "User ID is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(id = user_id)
    except User.DoesNotExist:
        return Response({"error":"User not found"}, status=status.HTTP_404_NOT_FOUND)

    user.is_blocked = not user.is_blocked
    user.save()

    return Response({"message":"User block status updated"}, status=status.HTTP_200_OK)

@api_view(['PUT'])
def verify_vendor(request):
    user_id = request.GET.get('id')

    if not user_id:
        return Response({'error':"User ID is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(id = user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    
    user.is_verified = True
    user.save()

    return Response({"message":"Vendor verified"})


class Categoryview(APIView):
    permission_classes = [IsAuthenticatedAndNotBlocked]
    def get(self,request):
        user = request.user

        if user and user.is_authenticated :
            categories = Categories.objects.all()
            serializer = CategorySerializer(categories, many = True)
            return Response(serializer.data, status = status.HTTP_200_OK) 
        
    
    def post(self, request):
        user = request.user

        if user and user.is_authenticated and user.role == 'admin':
            serializer = CategorySerializer(data = request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def put(self, request, id):
        user = request.user

        if user and user.is_authenticated and user.role == 'admin':
            try:
                category_instance = Categories.objects.get(id=id )
            except Categories.DoesNotExist:
                return Response({"error":"Category not found"}, status=status.HTTP_404_NOT_FOUND)
            serializer = CategorySerializer(category_instance, data = request.data, partial = True)

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status = status.HTTP_201_CREATED)
            return Response(serializer.errors, status= status.HTTP_400_BAD_REQUEST)
        return Response({"error":"Unauthorized"},status=status.HTTP_401_UNAUTHORIZED)
    

#coupons

class Coupons(APIView):
    permission_classes = [IsAdmin]

    def post(self, request):
        data = request.data

        try:
            serializer = CouponSerializer(data = data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  
        except Exception as e:
            return Response(
                {'error':str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get(self, request):
        coupons = Coupon.objects.all()
        response_main = []
        for coupon in coupons:
            response = {
                'id': coupon.id,
                'start_date': coupon.start_date,
                'expiry_date': coupon.expiry_date,
                'code': coupon.code,
                'discount_type': coupon.discount_type,
                'discount_value': coupon.discount_value,
                'max_discount': coupon.max_discount,
                'min_order_value': coupon.min_order_value,
                'is_active': coupon.is_active,
                'is_active_admin': coupon.is_active_admin,
            }
            response_main.append(response)

        
        return Response(response_main, status=status.HTTP_200_OK)

    def put(self, request, coupon_id):
        try: 
            coupon = Coupon.objects.get(id = coupon_id)
            
            serializer = CouponSerializer(coupon, data = request.data, partial = True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    

@api_view(['POST'])
def toggle(request, coupon_id):
    try:
        coupon = Coupon.objects.get(id = coupon_id)

        coupon.is_active_admin = request.data.get('is_active_admin')
        coupon.save()
        return Response({'message': 'Coupon status updated successfully'}, status=status.HTTP_200_OK)
    except Coupon.DoesNotExist:
        return Response({'error': 'Coupon not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error':str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



#orders

@api_view(['GET'])
@permission_classes([IsAdmin])
def admin_order_fetch(request):
    order_items = OrderItems.objects.order_by('-created_at')

    response_data_orders = []
    for item in order_items:
            shipping_address = item.order.order_shipping_address.first()
            product_image = item.variant.product.product_images.first()
            image_url = request.build_absolute_uri(product_image.image.url) if product_image else None
            if item.order_item_status == 'cancelled' and item.refund_status:
                payment_status = f"refund of {item.refund_amount} is {item.refund_status}"
            else:
                payment_status = item.order.order_payment.payment_status
            response_data_order = {
                'order_item_id':item.id,
                'payment_status': payment_status,
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
@permission_classes([IsAdmin])
def admin_order_status_update(request, order_item_id):
    admin = request.user
    new_status = request.data.get('status', '').lower()
    cancellation_reason = request.data.get('cancellation_reason', '')
    if new_status not in ['delivered', 'cancelled']:
        return Response({'error': 'This is an invalid status'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        with transaction.atomic():
            # Lock the order item to prevent concurrent updates
            order_item = OrderItems.objects.select_for_update().get(id=order_item_id)
            order = order_item.order
            payment = order.order_payment
            current_status = order_item.order_item_status

            if current_status == 'processing':
                return Response({'error': 'Item must be dispatched first'}, status=status.HTTP_400_BAD_REQUEST)

            if current_status == 'cancelled' and new_status == 'delivered':
                return Response({'error': 'Cancelled item cannot be delivered'}, status=status.HTTP_400_BAD_REQUEST)


            #Handle delivery            
            if new_status == 'delivered' and current_status == 'dispatched':
                if payment.payment_status == 'pending' and payment.payment_method == 'card':
                    return Response({'error': 'Payment pending'}, status=status.HTTP_400_BAD_REQUEST)
                
                order_item.order_item_status = new_status
                order_item.save()


                #handle COD payment completion
                if payment.payment_method == 'cod' and payment.payment_status == 'pending':
                    non_cancelled_items = order.order_items.exclude(order_item_status = 'cancelled', id = order_item.id)
                    if all(item.order_item_status == 'delivered' for item in non_cancelled_items):
                        payment.payment_status = 'completed'
                        payment.save()

                        admin_wallet, _ = Wallet.objects.get_or_create(user = admin)
                        admin_wallet.credit(order.final_price)
                        WalletTransactionsAdmin.objects.create(
                            user = admin,
                            amount = order.final_price,
                            transaction_type = 'credit',
                            transacted_user = order.customer.user,
                            transaction_through = 'cash'
                        )

                return Response({'success': True}, status = status.HTTP_200_OK)
            
            #Handle cancellation
            if new_status == 'cancelled' and current_status == 'dispatched':
                order_item.order_item_status = new_status
                order_item.cancel_reason = f"{cancellation_reason} - cancelled by {admin.email}"
                order_item.cancel_time = timezone.now()
                order_item.save()
                product_item = order_item.variant
                product_item.stock += order_item.quantity
                product_item.save()
                return Response({'success': True}, status = status.HTTP_200_OK)
            
    except OrderItems.DoesNotExist:
        return Response({'error': 'Order item not found'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    


#Admin Dashboard

@api_view(['GET'])
@permission_classes([IsAdmin])
def dashboardfetch(request):
    filter_type = request.query_params.get('filter', 'daily')
    valid_filters = ['daily', 'weekly', 'monthly']

    if filter_type not in valid_filters:
        return Response({'error': 'Invalid filter type. Use "daily", "weekly", or "monthly".'}, status=status.HTTP_400_BAD_REQUEST)

    dummy_obj = {}
    serializer = AdminDashboard(instance = dummy_obj, context= {'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAdmin])
def order_details_salesreport(request):
    try:

        filter_type = request.query_params.get('filter', 'daily')

        end_date = now()
        output_data = []
        if filter_type == 'daily':
            start_date = end_date - timedelta(days = 1)
        elif filter_type == 'weekly':
            start_date = end_date - timedelta(weeks=1)
        elif filter_type == 'monthly':
            start_date = end_date - timedelta(days = 30)
        else:
            start_date = end_date - timedelta(days=1)

        order_items = OrderItems.objects.filter(created_at__range = (start_date, end_date))
        for order_item in order_items:
            data = {
                'id': order_item.id,
                'vendor': order_item.variant.product.vendor.user.email,
                'company': order_item.variant.product.vendor.company_name,
                'quantity': order_item.quantity,
                'status': order_item.order_item_status,
                'vendor_amount_paid': order_item.is_payment_done_to_vendor,
                'vendor_paid_amount': order_item.payment_done_to_vendor,
            }
            output_data.append(data)
    except OrderItems.DoesNotExist:
        return Response({'error': 'No data found'}, status=status.HTTP_404_NOT_FOUND)

    return Response(output_data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAdmin])
def add_banner(request):
    data = request.data
    print('data for banner', data)

    serializer = BannerSerializer(data = data)
    try:
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status= status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def banner_fetch(request):
    banners = Banner.objects.filter(is_active_admin = True)
    response_main = [] 

    for banner in banners:
        response = {
            'id' : banner.id,
            'image':request.build_absolute_uri(banner.image.url),
            'start_date' : banner.start_date,
            'expiry_date' : banner.expiry_date,
            'is_active' : banner.is_active,
            'is_active_admin' :banner.is_active_admin,
        }
        response_main.append(response) 
    
    return Response(response_main, status=status.HTTP_200_OK)

@api_view(['DELETE'])
@permission_classes([IsAdmin])
def banner_remove(request, banner_id):
    banner = Banner.objects.get(id = banner_id)
    banner.is_active_admin = False
    banner.save()

    return Response({'success': True}, status=status.HTTP_200_OK)


@api_view(['PUT'])
@permission_classes([IsAdmin])
def banner_update(request, banner_id):
    banner = Banner.objects.get(id = banner_id)
    try:
        banner_serializer = BannerSerializer(banner, data = request.data, partial = True)
        if banner_serializer.is_valid():
            banner_serializer.save()    
            return Response(banner_serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(banner_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
@permission_classes([IsAdmin])
def admin_product_fetch(request):
    
    products = Products.objects.filter(is_deleted = False)
    
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
            'brand': product.vendor.company_name,
            'product_name':product.name,
            'product_image':image_url,
            'category': product.category.category,
            'variants': variant_data,
            'is_blocked':product.is_blocked 
        })


    paginator = CustomPagination()
    paginated_products = paginator.paginate_queryset(product_data, request)

    if paginated_products is not None:
        return paginator.get_paginated_response(paginated_products)
    return Response([])


@api_view(['POST'])
@permission_classes([IsAdmin])
def admin_product_block(request, product_id):
    try:
        product = Products.objects.get(id = product_id)
        product.is_blocked = not product.is_blocked
        product.save()
        return Response({'status': 'success', 'is_blocked': product.is_blocked}, status=status.HTTP_200_OK)
    except Products.DoesNotExist:
        return Response({'status': 'failure'}, status=status.HTTP_404_NOT_FOUND)