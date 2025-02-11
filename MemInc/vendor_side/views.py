from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import product_serializer

# Create your views here.

class Product_create_view(APIView):
    def post(self, request):
        print(request.user)
        print(request.COOKIES)
        if not request.user.is_authenticated or request.user.role != 'vendor':
            return Response({"error": "Only vendors can create products"}, status = status.HTTP_403_FORBIDDEN)
        serializer = product_serializer(data = request.data, context = {'request':request})
        print(request.data)
        if serializer.is_valid(raise_exception=True):
            product = serializer.save()
            return Response(product_serializer(product).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

            