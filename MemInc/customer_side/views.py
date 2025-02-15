from rest_framework.response import Response
from rest_framework import status
from vendor_side.models import Products
from rest_framework.decorators import api_view
from admin_side.views import CustomPagination
from authentication.serializers import CustomerSerializer


# Create your views here.


@api_view(['GET'])
def product_listing_customer_side(request):
    products = Products.objects.all()

    product_data = []
    for product in products:
        image_url = request.build_absolute_uri(product.product_images.first().image.url) 
        variants = product.variant_profile.all()
        variant_data = []
        for variant in variants:
            variant_data.append({
                'id': variant.id,
                'name': f'{variant.quantity} {variant.variant_unit}',
                'price': variant.price,
                'stock': variant.stock
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


@api_view(['POST'])
def customer_profile_update(request):
    user = request.user
    if not user.is_authenticated or user.is_blocked:
        return Response({"error":"Customer is not found"}, status=status.HTTP_404_NOT_FOUND)
    
    customer_instance = user.customer_profile

    serializer = CustomerSerializer(instance = customer_instance, data = request.data, partial = True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(serializer.data, status = status.HTTP_200_OK)
    
    
    
   