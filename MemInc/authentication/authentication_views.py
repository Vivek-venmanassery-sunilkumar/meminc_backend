
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import CustomerSerializer
from django.core.cache import cache
from django.core.mail import send_mail
import random



#RegisterCustomer post function to get the validated data, generate otp, send mail to the email and save the data in cache.
class RegisterCustomer(APIView):
    def post(self, request):
        serializer = CustomerSerializer(data = request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        registration_data = serializer.validated_data

        otp = ''.join([str(random.randint(0,9)) for i in range(6)])

        cache_key = f"registration_{registration_data['email']}"
        cache_data = {
            'registration_data': registration_data,
            'otp': otp
        }

        cache.set(cache_key,cache_data, timeout=60)

        send_mail(
            'Verify your Email',
            f'Your otp for registration into MemInc:Fresh to home is: {otp}. The otp is valid for only 1 minute so hurry up!',
            'meminccorporation.gmail.com',
            [registration_data['email']],
            fail_silently=False,
        )
        print(f"otp: {otp}")

        return Response({
            "message": "Please check your registered email for otp.",
            "email": registration_data['email']
        }, status=status.HTTP_201_CREATED)
        



