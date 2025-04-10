from rest_framework import serializers
from .models import Coupon, Banner
from django.utils.timezone import now
from datetime import timedelta
from cart_and_orders.models import Order, OrderItems
from wallet.models import CommissionRecievedAdminPerOrder, WalletTransactionsVendor
from authentication.models import CustomUser
from django.db.models import Sum
from authentication.models import Vendor

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = '__all__'
        extra_kwargs = {
            'is_active': {'required': False},
            'is_active_admin': {'required': False}
        }

    def validate_start_date(self, value):

        current_date =  now().date()

        if value < current_date:
            raise serializers.ValidationError("Start date cannot be in the past.")
        
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
    

class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = '__all__'    
        extra_kwargs = {
            'is_active': {'required': False},
            'is_active_admin': {'required': False, 'default': True}
        }

    def validate_start_date(self, value):
        if value < now().date():
            raise serializers.ValidationError("Start date cannot be in the past.")
        return value

    def validate(self, data):
        start_date = data.get('start_date')
        expiry_date = data.get('expiry_date')

        if expiry_date <= start_date:
            raise serializers.ValidationError('Expiry date must be after start date')
        
        return data
    
    def save(self, **kwargs):
        current_date = now().date()

        start_date = self.validated_data.get('start_date')
        if start_date == current_date:
            self.validated_data['is_active'] = True
        else:
            self.validated_data['is_active'] = False
        
        return super().save(**kwargs)

class AdminDashboard(serializers.Serializer):
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2, read_only = True)
    total_commission_earned = serializers.DecimalField(max_digits=10, decimal_places=2, read_only = True)
    total_vendor_earnings = serializers.DecimalField(max_digits=10, decimal_places=2, read_only = True)
    total_customers_active = serializers.IntegerField(read_only = True)
    total_vendors_active = serializers.IntegerField(read_only = True)
    pending_orders = serializers.IntegerField(read_only  = True)
    vendor_payouts_pending = serializers.IntegerField(read_only = True)
    most_active_vendor = serializers.CharField(max_length=100, read_only = True)
    discounts_given = serializers.DecimalField(max_digits=10, decimal_places=2, read_only = True)

    def to_representation(self, instance):
        print('to representation')

        request = self.context.get('request')
        filter_type = request.query_params.get('filter', 'daily')

        end_date = now()
        if filter_type == 'daily':
            start_date = end_date - timedelta(days = 1)
        elif filter_type == 'weekly':
            start_date = end_date - timedelta(weeks=1)
        elif filter_type == 'monthly':
            start_date = end_date - timedelta(days = 30)
        else:
            start_date = end_date - timedelta(days=1)

        
        total_revenue = Order.objects.filter(delivered_at__range=(start_date, end_date), order_status = 'delivered').aggregate(total = Sum('final_price'))['total'] or 0
        total_commission_earned = CommissionRecievedAdminPerOrder.objects.filter(timestamp__range = (start_date, end_date)).aggregate(total = Sum('commission_kept'))['total'] or 0
        total_vendor_earnings = WalletTransactionsVendor.objects.filter(timestamp__range = (start_date, end_date)).aggregate(total = Sum('amount'))['total'] or 0
        total_customers_active = CustomUser.objects.filter(role= 'customer', is_active = True).count() or 0
        total_vendors_active = CustomUser.objects.filter(role = 'vendor', is_active = True).count() or 0
        pending_orders = OrderItems.objects.exclude(order_item_status__in = ['cancelled', 'delivered']).filter(created_at__range = (start_date, end_date)).count() or 0
        vendor_payouts_pending = OrderItems.objects.filter(order_item_status = 'delivered', is_payment_done_to_vendor= False).count() or 0
        most_active_vendor = OrderItems.objects.filter(order_item_status = 'delivered', created_at__range = (start_date, end_date)).values('variant__product__vendor').annotate(total_items_sold = Sum('quantity')).order_by('-total_items_sold').first()
        discounts_given  = Order.objects.filter(order_status = 'delivered', created_at__range = (start_date,end_date)).aggregate(total = Sum('discount_price'))['total'] or 0        

        try:
            vendor_id = most_active_vendor.get('variant__product__vendor')
        except (AttributeError, KeyError):
            vendor_id = None

        if vendor_id:
            vendor = Vendor.objects.get(id = vendor_id)
            vendor_name = vendor.first_name
        else:
            vendor_name = 'mandan'
        data = {
            'total_revenue': total_revenue,
            'total_commission_earned': total_commission_earned,
            'total_vendor_earnings': total_vendor_earnings,
            'total_customers_active': total_customers_active,
            'total_vendors_active': total_vendors_active,
            'pending_orders': pending_orders,
            'vendor_payouts_pending': vendor_payouts_pending,
            'most_active_vendor': vendor_name,
            'discounts_given': discounts_given
        }
        print(f"data: {data}")

        return data


