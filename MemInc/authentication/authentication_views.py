
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
            'otp': otp,
            'attempts': 1
        }

        cache.set(cache_key,cache_data, timeout=120)

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
            "email": registration_data['email'],
            'resend_attempts_remaining': 2
        }, status=status.HTTP_200_OK)
        

class ResendOtp(APIView):
    def post(self, request):
        email = request.data['email']
        cache_key = f'registration_{email}'
        cache_data = cache.get(cache_key)
        if not cache_data:
            return Response({'error': 'Registration session expired.Try again','registration_timeout': True}, status=status.HTTP_400_BAD_REQUEST)
        attempts = cache_data['attempts']
        if attempts > 2:
            return Response({
                'error':'Registration attempts for the current session expired.Try again.',
                'registration_timeout': True
            }, status= status.HTTP_429_TOO_MANY_REQUESTS)
        
        new_otp = ''.join(str(random.randint(0,9)) for i in range(0,6))
        registration_data = cache_data['registration_data']
        new_cache_data = {
            'registration_data': registration_data,
            'otp': new_otp,
            'attempts': attempts + 1
        }
        cache.set(cache_key, new_cache_data, timeout=120)

        send_mail(
            'Verify your Email',
            f"Your otp for registration into MemInc:Fresh to home is: {new_otp}. The otp is valid for 1 minute.",
            'meminccorporation@gmail.com',
            [email],
            fail_silently=False,
        )
        print(f"resend_otp: {new_otp}, resend attempts remaining: {3 - attempts}")
        return Response({
            "message": "Please check your registered email for otp.",
            'registered_email': email,
            'resend_attempts_remaining': 3-attempts+1
        }, status=status.HTTP_200_OK)
        
        

class CustomerOtpValidation(APIView):
    def post(self, request):
        data = request.data
        print(data)
        return Response({"message":"checking for data."}, status=status.HTTP_201_CREATED)



