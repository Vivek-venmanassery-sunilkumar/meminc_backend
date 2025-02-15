from rest_framework.decorators import api_view
from authentication.models import Customer, Vendor
from rest_framework.pagination import PageNumberPagination 
from rest_framework.response import Response
from rest_framework import status
import math
from django.contrib.auth import get_user_model

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