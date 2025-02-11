from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        token = request.COOKIES.get('access_token')
        print("Token from cookie:", token)

        if not token:
            print("No token found in cookies")
            return None
        
        try:
            validated_token = self.get_validated_token(token)
            user = self.get_user(validated_token)
            print("User authenticated:", user)
            return (user, validated_token)
        except InvalidToken as e:
            print("Invalid token error:", e)
            return None 