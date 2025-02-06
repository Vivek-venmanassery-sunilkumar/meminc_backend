
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import CustomerSerializer


class RegisterCustomer(APIView):
    def post(self, request):
        serializer = CustomerSerializer(data = request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({"message":"Customer Registration Successfull.", 'data': serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

