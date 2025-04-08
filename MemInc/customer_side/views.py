from rest_framework.response import Response
from rest_framework import status
from vendor_side.models import Products, ProductVariants
from rest_framework.decorators import api_view, permission_classes
from admin_side.views import CustomPagination
from authentication.serializers import CustomerSerializer
from .serializers import CustomerAddressSerializer
from rest_framework.views import APIView
from authentication.permissions import IsAuthenticatedAndNotBlocked,IsCustomer
from authentication.models import CustomerAddress
from admin_side.models import Coupon, UsedCoupon
from decimal import Decimal
from cart_and_orders.models import OrderItems
from django.utils import timezone
from cart_and_orders.models import Order
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration

# Create your views here.


@api_view(['GET'])
def product_listing_customer_side(request):
    products = Products.objects.all().order_by('-created_at')

    product_data = []
    for product in products:
        if product.is_deleted == False:
            if product.category.is_enabled: 
                image_url = request.build_absolute_uri(product.product_images.first().image.url) 
                variants = product.variant_profile.all()
                variant_data = []
                for variant in variants:
                    if variant.is_deleted == False:
                        variant_data.append({
                            'id': variant.id,
                            'name': f'{variant.variant_unit} {variant.quantity}' if variant.variant_unit == 'packet of' else f'{variant.quantity} {variant.variant_unit}',
                            'price': variant.price,
                            'stock': variant.stock,
                            'is_out_of_stock': variant.stock == 0,
                        })
                product_data.append({
                    'id':product.id,
                    'product_name':product.name,
                    'product_image':image_url,
                    'category': product.category.category,
                    'company_name': product.vendor.company_name,
                    'variants': variant_data
                })


    paginator = CustomPagination()
    paginated_products = paginator.paginate_queryset(product_data, request)

    if paginated_products is not None:
        return paginator.get_paginated_response(paginated_products)
    return Response([])


@api_view(['PATCH'])
@permission_classes([IsCustomer])
def customer_profile_update(request):
    user = request.user
    
    customer_instance = user.customer_profile
    serializer = CustomerSerializer(instance = customer_instance, data = request.data, partial = True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    response = Response({
         'role': user.role,
         'first_name': user.customer_profile.first_name,
         'last_name': user.customer_profile.last_name,
         'email': user.email,
         'phone_number': user.customer_profile.phone_number,
         'profile_picture': request.build_absolute_uri(user.customer_profile.profile_picture.url) if user.customer_profile.profile_picture else None,
    },status=status.HTTP_200_OK)
    return response
    
    
# view functions for the crud operations on customer addresses    

class AddressManagementCustomer(APIView):
    
    permission_classes = [IsAuthenticatedAndNotBlocked]
    def post(self, request):
        address_data = request.data

        customer = request.user.customer_profile
        address_serializer = CustomerAddressSerializer(data= address_data)

        if not address_serializer.is_valid():
            return Response(address_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        address_serializer.save(customer = customer)

        return Response(address_serializer.data,status=status.HTTP_201_CREATED)
    

    def get(self, request, address_id = None):
        if address_id is not None:
            try:
                address_data = CustomerAddress.objects.get(id = address_id, customer= request.user.customer_profile)
                serializer = CustomerAddressSerializer(address_data)
                return Response(serializer.data, status = status.HTTP_200_OK)
            except CustomerAddress.DoesNotExist:
                return Response({'message':'Address does not exist'}, status=status.HTTP_404_NOT_FOUND)
        
        else:
            address_data = CustomerAddress.objects.filter(customer = request.user.customer_profile)
            serializer = CustomerAddressSerializer(address_data, many= True)
            return Response(serializer.data, status=status.HTTP_200_OK) 
        

    def put(self, request, address_id):
        try:
            address_data = CustomerAddress.objects.get(id = address_id, customer = request.user.customer_profile)
            serializer = CustomerAddressSerializer(address_data, data=request.data, partial = True)

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except CustomerAddress.DoesNotExist:
            return Response({"error":"Address not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error":str(e)},status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def delete(self, request, address_id):
        try:
            address_data = CustomerAddress.objects.get(id = address_id, customer = request.user.customer_profile)
            address_data.delete()
            return Response({'message': 'Address deleted successfully'}, status=status.HTTP_200_OK)
        except CustomerAddress.DoesNotExist:
            return Response({'error':'Address not found'}, status=status.HTTP_404_NOT_FOUND)
        



@api_view(['GET'])
@permission_classes([IsCustomer])
def customer_coupons(request):
    try:
        total_price = request.GET.get('total_price')
        coupons = Coupon.objects.filter(is_active = True, is_active_admin = True)
        used_coupon_instance = UsedCoupon.objects.filter(user = request.user)
        used_coupons = []
        for used_coupon in used_coupon_instance:
            used_coupons.append(used_coupon.coupon)
        response= []
        for coupon in coupons:
            if coupon not in used_coupons:
                if Decimal(total_price) >= coupon.min_order_value:
                    response_coupon = {
                        'id': coupon.id,
                        'code': coupon.code,
                        'coupon_type': coupon.discount_type,
                        'discount_value': coupon.discount_value,
                        'max_discount': coupon.max_discount,
                        'min_order_value': coupon.min_order_value,
                    }
                    response.append(response_coupon)
        
        return Response(response, status=status.HTTP_200_OK)
    except Coupon.DoesNotExist:
        return Response({'message':'No available coupons'}, status=status.HTTP_400_BAD_REQUEST)



@api_view(['PATCH'])
@permission_classes([IsCustomer])
def customer_order_item_cancel(request, order_id, order_item_id):
    customer = request.user.customer_profile
    order_item = OrderItems.objects.get(id = order_item_id)
    cancellation_reason = request.data.get('cancellation_reason')

    order_item.order_item_status = 'cancelled'
    order_item.cancel_reason = f"{cancellation_reason} - cancelled by {customer.first_name}"
    order_item.cancel_time = timezone.now()
    order_item.save()
    return Response({'success': True}, status = status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticatedAndNotBlocked])
def product_filter_customer(request):
    categories = []
    if 'categories' in request.GET:
        categories = [cat for cat in request.GET['categories'].split(',') if cat] if ',' in request.GET['categories'] else request.GET.getlist('categories')
    
    brands = []
    if 'brands' in request.GET:
        brands = [bra for bra in request.GET['brands'].split(',') if bra] if ',' in request.GET['brands'] else request.GET.getlist('brands')
    min_price = request.GET.get('min_price', 0)
    max_allowed_price = 10000
    max_price = request.GET.get('max_price', max_allowed_price)
    search_term = request.GET.get('search', None)
    products = Products.objects.filter(is_deleted = False)
    

    if categories:
        products = products.filter(category__id__in = categories)
    
    if brands:
        products = products.filter(vendor__company_name__in = brands)
    
    if search_term:
        products = products.filter(name__icontains = search_term)

    variants = ProductVariants.objects.filter(
        price__gte = min_price,
        price__lte = max_price,
        is_deleted = False,
    )

    product_ids = variants.values_list('product_id', flat=True).distinct()

    products = products.filter(id__in = product_ids)

    product_data = []
    for product in products:
        image_url = request.build_absolute_uri(product.product_images.first().image.url) if product.product_images.first() else None
        variants = product.variant_profile.filter(is_deleted = False)
        variant_data = []
        for variant in variants:
            variant_data.append({
                'id': variant.id,
                'name': f'{variant.variant_unit} {variant.quantity}' if variant.variant_unit == 'packet of' else f'{variant.quantity} {variant.variant_unit}',
                'price': variant.price,
                'stock': variant.stock,
                'is_out_of_stock': variant.stock == 0,
            })

        product_data.append({
            'id': product.id,
            'product_name': product.name,
            'product_image': image_url,
            'category': product.category.category,
            'company_name': product.vendor.company_name,
            'variants': variant_data,
        })

    paginator = CustomPagination()
    paginated_products = paginator.paginate_queryset(product_data, request)

    if paginated_products is not None:
        return paginator.get_paginated_response(paginated_products)
    return Response([])

@api_view(['GET'])
def product_fetch_non_customer(request):
    products = Products.objects.all()
    product_data = []
    for product in products:
        image_url = request.build_absolute_uri(product.product_images.first().image.url) if product.product_images.first() else None
        variants = product.variant_profile.filter(is_deleted = False)
        variant_data = []
        for variant in variants:
            variant_data.append({
                'id': variant.id,
                'name': f'{variant.variant_unit} {variant.quantity}' if variant.variant_unit == 'packet of' else f'{variant.quantity} {variant.variant_unit}',
                'price': variant.price,
                'stock': variant.stock,
                'is_out_of_stock': variant.stock == 0,
            })

        product_data.append({
            'id': product.id,
            'product_name': product.name,
            'product_image': image_url,
            'category': product.category.category,
            'company_name': product.vendor.company_name,
            'variants': variant_data,
        })

    paginator = CustomPagination()
    paginated_products = paginator.paginate_queryset(product_data, request)

    if paginated_products is not None:
        return paginator.get_paginated_response(paginated_products)
    return Response([])


@api_view(['GET'])
@permission_classes([IsCustomer])
def invoice_generate(request, order_id):
    order = Order.objects.get(id = order_id)
    order_items = OrderItems.objects.filter(order = order)

    order_item_data = []
    for order_item in order_items:
        data = {
            'id': order_item.id,
            'product': f'{order_item.variant.product.name}, {order_item.variant.variant_unit} {order_item.variant.quantity}' if order_item.variant.variant_unit == 'packet of'
                        else f'{order_item.variant.product.name}, {order_item.variant.quantity} {order_item.variant.variant_unit}',
            'quantity': order_item.quantity,
            'price': order_item.price,
            'order_item_status': order_item.order_item_status,
            'refund_amount': {order_item.refund_amount} if order_item.order_item_status == 'cancelled' else 'No refund',
        }
        order_item_data.append(data)
    
    invoice_data = {
        'id': order.id,
        'order_amount': order.final_price,
        'discount_price': order.discount_price,
        'order_item_data': order_item_data,
    }

    #render html template

    html_string = render_to_string('customerinvoice/invoice.html', {
        'invoice_data': invoice_data,
        'order_date': order.created_at.strftime("%B %d, %Y"),
        'order_status': order.order_status,
        'subtotal': order.total_price,
    })

    
    #create pdf
    font_config = FontConfiguration()
    html = HTML(string = html_string)
    result = html.write_pdf(font_config = font_config)

    #send email with pdf attachment
    try:
        subject = f"Your invoice for Order #{order.id}"
        message = f"Please find attached invoice for your recent order #{order.id}." 
        email = EmailMessage(
            subject,
            message,
            'meminccorporation@gmail.com',
            [request.user.email],
        )

        email.attach(f'invoice_{order.id}.pdf', result, 'application/pdf')
        email.send()
    except Exception as e:
        return Response(
            {'error': 'Invoice generated but failed to send email', 'details': str(e)},
            status = status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return Response({
        'message': 'Invoice generated and sent successfully'
    },status=status.HTTP_200_OK)

