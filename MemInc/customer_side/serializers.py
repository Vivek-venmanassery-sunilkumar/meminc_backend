from authentication.models import CustomerAddress
from rest_framework import serializers
import re

class CustomerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerAddress
        fields = ['id','street_address', 'state', 'country', 'pincode', 'city']

    def validate_pincode(self, value):
        if not re.fullmatch(r'^\d{6}$', str(value)):
            raise serializers.ValidationError('Pincode should be of 6 digits')
        return value
            