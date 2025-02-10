from rest_framework.decorators import api_view
from authentication.models import Customer, Vendor
from rest_framework.pagination import PageNumberPagination 
from rest_framework.response import Response
import math

class custom_pagination(PageNumberPagination):
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
    paginator = custom_pagination()
    paginated_customers =  paginator.paginate_queryset(customers, request)
    print(paginated_customers)
    
    if paginated_customers is not None:
        return paginator.get_paginated_response(paginated_customers)    
    return Response([])

@api_view(['GET'])
def list_vendor(request):
    vendors = Vendor.objects.select_related('user')
    paginator = custom_pagination()
    paginated_vendors = paginator.paginate_queryset(vendors, request)

    if paginated_vendors is not None:
        return paginator.get_paginated_response(paginated_vendors)
    return Response([])