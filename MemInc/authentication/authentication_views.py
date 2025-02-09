
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import CustomerSerializer,VendorSerializer
from django.core.cache import cache
from django.core.mail import send_mail
import random
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken




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
            'role':'customer',
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
        
class RegisterVendor(APIView):
    def post(self, request):
        vendor = VendorSerializer(data = request.data)
        if not vendor.is_valid():
            return Response(vendor.errors, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        registration_data = vendor.validated_data

        otp = ''.join(str(random.randint(0,9)) for i in range(0,6))
        cache_key = f"registration_{registration_data['email']}"
        cache_data = {
            'registration_data': registration_data,
            'otp': otp,
            'role': 'vendor',
            'attempts': 1
        }
        cache.set(cache_key, cache_data, timeout=120)

        send_mail(
            'Verify Your Email',
            f"Hai precious, your otp for registration into Meminc:Fresh to home is {otp}. The otp is valid only for 1 min so hurry up!",
            'meminccorporation@gmail.com',
            [registration_data['email']],
            fail_silently=False,
        )
        
        print("VendorOtp:", otp)

        return Response({
            'message':"Please check your registered email for otp.",
            'email': registration_data['email'],
            'resend_attempts_remaining': 2
        })


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

        if cache_data['role'] == 'customer':
            new_cache_data = {
                'registration_data': registration_data,
                'otp': new_otp,
                'role': 'customer',
                'attempts': attempts + 1
            }
        elif cache_data['role'] == 'vendor':
            new_cache_data = {
                'registration_data': registration_data,
                'otp': new_otp,
                'role': 'vendor',
                'attempts':attempts + 1
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
        
        

class OtpValidation(APIView):
    def post(self, request):
        email = request.data['email']
        cache_key = f"registration_{email}"
        cache_data = cache.get(cache_key)
        print("cache_data:",cache_data)
        otp = request.data['otp']
        print("recieved otp from the request",otp)
        if not cache_data:
            return Response({'error': 'Registration session expired.Please Register again!','registration_timeout':True}, status=status.HTTP_400_BAD_REQUEST)

        if str(cache_data['otp']).strip() != str(otp).strip():
            return Response({"error": "Invalid otp", "is_eql": cache_data['otp'] == otp}, status = status.HTTP_404_NOT_FOUND)
        
        registration_data = cache_data['registration_data']

        if cache_data['role'] == 'customer':
            print(registration_data)
            customer = CustomerSerializer(data = registration_data)
            if not customer.is_valid():
                return Response(customer.errors, status=status.HTTP_400_BAD_REQUEST)

            customer.save()
        elif cache_data['role'] == 'vendor':
            print(registration_data)
            vendor = VendorSerializer(data = registration_data)
            if not vendor.is_valid():
                return Response({vendor.errors}, status=status.HTTP_400_BAD_REQUEST)
            vendor.save()
            
        return Response({"message":"checking for data."}, status=status.HTTP_201_CREATED)



class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(request, username = email, password = password)
        print("user:", user)

        if user is not None:
            if not user.is_blocked and user.is_verified:
                refresh = RefreshToken.for_user(user)
                access_token = refresh.access_token

                access_token['role'] = user.role
                if user.role == 'customer':
                    first_name = user.customer_profile.first_name
                    last_name = user.customer_profile.last_name
                elif user.role == 'vendor':
                    first_name = user.vendor_profile.first_name
                    last_name = user.vendor_profile.last_name
                elif user.role == 'admin':
                    print("I am admin")
                    response = Response({
                        'message': 'Login successfull',
                        'role': user.role,
                        'first_name': 'admin',
                        'last_name': 'admin'
                    }, status=status.HTTP_200_OK)

                    response.set_cookie(
                    key = 'access_token',
                    value = str(access_token),
                    httponly = True,
                    path = '/',
                    secure = False,
                    max_age = 60*15,
                    samesite='Lax',
                    )

                    response.set_cookie(
                        key = 'refresh_token',
                        value = str(refresh),
                        path='/',
                        httponly = True,
                        samesite='Lax',
                        secure = False,
                        max_age=60*60*24*7,
                    )
                    return response

                response = Response({
                    'message':'Login successfull',
                    'role': user.role,
                    'first_name': first_name,
                    'last_name': last_name
                }, status = status.HTTP_200_OK)
                
                response.set_cookie(
                    key = 'access_token',
                    value = str(access_token),
                    httponly = True,
                    path = '/',
                    secure = False,
                    max_age = 60*15,
                    samesite='Lax',
                )

                response.set_cookie(
                    key = 'refresh_token',
                    value = str(refresh),
                    path='/',
                    httponly = True,
                    samesite='Lax',
                    secure = False,
                    max_age=60*60*24*7,
                )
                return response
            else:
                print("ithaano error")
                return Response({'error': 'You are not authorized by the admin.Please wait'}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({'error': 'Invalid Credentials'}, status=status.HTTP_401_UNAUTHORIZED)