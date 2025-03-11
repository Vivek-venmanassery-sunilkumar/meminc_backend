from rest_framework.decorators import api_view
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
        coupon = Coupon.objects.get(id = coupon_id)

        pass
