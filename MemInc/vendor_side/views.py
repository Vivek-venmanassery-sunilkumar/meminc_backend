import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import product_serializer
from rest_framework.parsers import MultiPartParser, FormParser
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
    

            