from rest_framework import serializers
from .models import Coupon
from django.utils.timezone import now

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = '__all__'
        extra_kwargs = {
            'is_active': {'required': False},
            'is_active_admin': {'required': False}
        }

    def validate_start_date(self, value):
        try:
            start_date = value
        except ValueError:
            raise serializers.ValidationError("Invalid date format for start date. Please use YYYY-MM-DD")

        current_date =  now().date()

        if start_date < current_date:
            raise serializers.ValidationError("Start date must be after or from today")
        
        return value
    
    def validate_expiry_date(self, value):
        try:
            expiry_date = value
        except ValueError:
            raise serializers.ValidationError("Invalid date format for expiry date. Please use YYYY-MM-DD")
        
        return value
    
    def validate(self, data):
        start_date = data.get('start_date')
        expiry_date = data.get('expiry_date')

        if expiry_date <= start_date:
            raise serializers.ValidationError('Expiry date must be after start date.')
        
        return data

    def save(self, **kwargs):
        current_date = now().date()

        start_date = self.validated_data.get('start_date')
        if start_date == current_date:
            self.validated_data['is_active'] = True
        else:
            self.validated_data['is_active'] = False
        
        return super().save(**kwargs)
    
