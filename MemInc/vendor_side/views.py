import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import product_serializer
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view
from authentication.models import Vendor
from admin_side.views import custom_pagination
# Create your views here.

class Product_create_view(APIView):
    parser_classes = (MultiPartParser, FormParser)
    def post(self, request):
        print(request.user)
        print(request.COOKIES)
        if not request.user.is_authenticated or request.user.role != 'vendor':
            return Response({"error": "Only vendors can create products"}, status = status.HTTP_403_FORBIDDEN)
        
        variants_data = request.data.get('variants', [])
        if isinstance(variants_data, str):
            variants_data = json.loads(variants_data)
        
        product_data = {
            'name': request.data.get('name'),
            'category': request.data.get('category'),
            'description': request.data.get('description'),
            'variant_unit': request.data.get('variant_unit'),
            'image': request.FILES.get('image'),
            'variants':variants_data
        }
        serializer = product_serializer(data = product_data, context = {'request':request})
        print(request.data)
        if serializer.is_valid(raise_exception=True):
            product = serializer.save()
            return Response(product_serializer(product).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
def product_listing_vendor(request):
    user = request.user
    print("vendor_side_product_listing debug: ",user)

    if not user.is_authenticated or user.is_blocked:
        return Response({'error': 'The vendor is not authenticated.'}, status=status.HTTP_401_UNAUTHORIZED)
    
    try:
        vendor = user.vendor_profile
        print(vendor)
    except Vendor.DoesNotExist:
        return Response({'error': 'Vendor not found'}, status=status.HTTP_404_NOT_FOUND)
    
    products = vendor.vendor_products.all()
    
    product_data = []
    for product in products:
        image_url = request.build_absolute_uri(product.image.url) if product.image else None
        variants = product.variant_profile.all()
        variant_data = []
        for variant in variants:
            variant_data.append({
                'id': variant.id,
                'name': f'{variant.quantity} {product.variant_unit}',
                'price': variant.price,
                'stock': variant.stock
            })
        product_data.append({
            'product_name':product.name,
            'product_image':image_url,
            'category': product.category.category,
            'variants': variant_data
        })


    paginator = custom_pagination()
    paginated_products = paginator.paginate_queryset(product_data, request)

    if paginated_products is not None:
        return paginator.get_paginated_response(paginated_products)
    return Response([])
            