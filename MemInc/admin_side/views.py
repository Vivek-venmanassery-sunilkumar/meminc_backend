from rest_framework.decorators import api_view, permission_classes
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
from authentication.permissions import IsAdmin
from .serializers import CouponSerializer
from .models import Coupon
from wallet.models import Wallet, WalletTransactionsAdmin
from django.db import transaction


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
    customers =Customer.objects.select_related('user').values('first_name', 'last_name', 'phone_number', 'user__id', 'user__is_blocked', 'user__email')
    paginator = CustomPagination()
    paginated_customers =  paginator.paginate_queryset(customers, request)
    
    if paginated_customers is not None:
        return paginator.get_paginated_response(paginated_customers)    
    return Response([])

@api_view(['GET'])
def list_vendor(request):
    vendors = Vendor.objects.select_related('user').values('first_name', 'last_name', 'phone_number', 'user__id', 'user__is_blocked','user__email','user__is_verified','company_name')
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
    if new_status not in ['delivered', 'cancelled']:
        return Response({'error': 'This is an invalid status'}, status=status.HTTP_400_BAD_REQUEST)
    
    if new_status == 'cancelled':
        cancellation_reason = request.data.get('cancellation_reason')

    try:
        with transaction.atomic():
            # Lock the order item to prevent concurrent updates
            order_item = OrderItems.objects.select_for_update().get(id=order_item_id)
            current_status = order_item.order_item_status

            if current_status == 'processing':
                return Response({'error': 'Vendor has to dispatch for further actions'}, status=status.HTTP_400_BAD_REQUEST)
            
            elif current_status == 'dispatched' and new_status == 'delivered':
                if order_item.order.order_payment.payment_status == 'pending' and order_item.order.order_payment.payment_method == 'card':
                    return Response({'error': 'Payment is not done yet'}, status=status.HTTP_400_BAD_REQUEST)

                elif order_item.order.order_payment.payment_status == 'completed':
                    order_item.order_item_status = new_status
                    order_item.save()
                    return Response({'success': True}, status=status.HTTP_200_OK)
                
                elif order_item.order.order_payment.payment_status == 'pending' and order_item.order.order_payment.payment_method == 'cod':
                    order_item.order_item_status = new_status
                    order_item.save()

                    order = order_item.order
                    order.update_order_status()

                    if order.order_status == 'delivered':
                        payment = Payments.objects.get(order=order)
                        if payment.payment_status != 'completed':
                            payment.payment_status = 'completed'
                            payment.save()

                            admin_wallet,created = Wallet.objects.get_or_create(user=admin)
                            admin_wallet.credit(amount=order.final_price)

                            WalletTransactionsAdmin.objects.create(
                                user=admin,
                                amount=order.final_price,
                                transaction_type='credit',
                                transacted_user=order.customer.user,
                                transaction_through='cash deposited in bank by partner',
                            )
                    return Response({'success': True}, status=status.HTTP_200_OK)
            
            elif current_status == 'cancelled' and new_status == 'delivered':
                return Response({'error': 'Order has already been cancelled and now is returned to respective vendor'}, status=status.HTTP_400_BAD_REQUEST)
            
            elif current_status == 'dispatched' and new_status == 'cancelled':
                order_item.order_item_status = new_status
                order_item.cancel_reason = f"{cancellation_reason} cancelled by {admin}"
                order_item.save()

                order = order_item.order
                order.update_order_status()

                if order.order_status == 'delivered':
                    payment = Payments.objects.get(order=order)
                    if payment.payment_status != 'completed' and payment.payment_method == 'cod':
                        payment.payment_status = 'completed'
                        payment.save()

                        admin_wallet = Wallet.objects.get(user=admin)
                        admin_wallet.credit(amount=order.final_price)

                        WalletTransactionsAdmin.objects.create(
                            user=admin,
                            amount=order.final_price,
                            transaction_type='credit',
                            transacted_user=order.customer.user.email,
                            transacted_through='cash deposited in bank by partner',
                        )
                        return Response({'success': True}, status=status.HTTP_200_OK)
                    
                    elif payment.payment_status != 'completed' and payment.payment_method == 'card':
                        return Response({'error': 'Payment not done'}, status=status.HTTP_400_BAD_REQUEST)
                
                return Response({'success': True}, status=status.HTTP_200_OK)

    except OrderItems.DoesNotExist:
        return Response({'error': 'The item is not found'}, status=status.HTTP_404_NOT_FOUND)