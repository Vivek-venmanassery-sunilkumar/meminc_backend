from rest_framework import serializers;
from authentication.models import Customer

# class customer_display_serializer(serializers.ModelSerializer):
#     user_id = serializers.IntegerField(source = 'user.id', read_only = True)
#     email = serializers.EmailField(source = 'user.email', read_only = True)
#     is_blocked = serializers.BooleanField(source ='user.is_blocked', read_only = True)
    
#     class Meta:
#         model = Customer

#         fields = ['user_id', 'first_name','last_name','email','phone_number','is_blocked']
