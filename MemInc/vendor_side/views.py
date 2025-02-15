import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ProductSerializer
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view
from authentication.models import Vendor
from admin_side.views import CustomPagination
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
        product_image_instance = product.product_images.first()
        image_url = request.build_absolute_uri(product_image_instance.image.url)
        variants = product.variant_profile.all()
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
            