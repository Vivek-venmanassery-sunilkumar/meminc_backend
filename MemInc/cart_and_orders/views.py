from django.forms.models import model_to_dict
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from authentication.permissions import IsAuthenticatedAndNotBlocked, IsCustomer
from .models import Cart, CartItems
from vendor_side.models import Products, ProductImages, ProductVariants
from authentication.models import Vendor, CustomerAddress
from rest_framework.response import Response
from rest_framework import status
from .models import *
from django.db import transaction
from decimal import Decimal
# Create your views here.


class CartDetails(APIView):
    permission_classes = [IsAuthenticatedAndNotBlocked, IsCustomer]

    def get(self, request):
        cart = get_object_or_404(Cart, user = request.user)

        cart_items = CartItems.objects.filter(cart = cart)

        items_data = []

        for item in cart_items:
            variant = item.variant
            product = variant.product
            vendor = product.vendor

            product_image= product.product_images.first()
            image_url =request.build_absolute_uri(product_image.image.url) if product_image else None
            variant_name = f"{variant.variant_unit} {variant.quantity}" if variant.variant_unit == 'packet of' else f"{variant.quantity} {variant.variant_unit}"


            item_data = {
                'variant_id': variant.id,
                'product_id': product.id,
                'product_name': product.name,
                'product_image': image_url,
                'variant_name':variant_name,
                'price': str(variant.price),
                'quantity': item.quantity,
                'brand': vendor.company_name
            }
            items_data.append(item_data)

        total_price = cart.calculate_total_price()

        response_data = {
            'user': cart.user.id,
            'items': items_data,
            'total_price': str(total_price),
        }

        return Response(response_data, status=status.HTTP_200_OK)

    def post(self, request):
        cart, created = Cart.objects.get_or_create(user = request.user)

        variant_id = request.data.get('variant_id')

        if not variant_id:
            return Response({'error': 'Varint ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        variant = get_object_or_404(ProductVariants, id = variant_id)

        if variant.stock <= 0:
            return Response({'error': 'This variant is out of stock'}, status=status.HTTP_400_BAD_REQUEST)
        

        cart_item, created = CartItems.objects.get_or_create(cart = cart, variant = variant)
        action = request.data.get('action')
        if not action:
            action = 'increase'

        if not created:
            if action == 'increase':
                if cart_item.quantity < variant.stock:
                    cart_item.quantity += 1
                    cart_item.save()
                else:
                    return Response({'error': 'product max stock availability reached'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                if cart_item.quantity == 1:
                    cart_item.delete()
                    return Response({'message': 'Item removed from cart'}, status=status.HTTP_204_NO_CONTENT)
                else:
                    cart_item.quantity -= 1
                    cart_item.save()
            
        print("cart_items object: ", cart_item)
        total_price = cart.calculate_total_price()

        updated_item = {
            'variant_id': variant.id,
            'product_id': variant.product.id, 
            'product_name': variant.product.name,
            'product_image': request.build_absolute_uri(variant.product.product_images.first().image.url),
            'variant_name': f"{variant.quantity} {variant.variant_unit}",
            'price': str(variant.price),
            'quantity': cart_item.quantity,
            'brand': variant.product.vendor.company_name,
        }

        response_data = {
            'updated_item' : updated_item, 
            'total_price':str(total_price)
        }

        return Response(response_data, status = status.HTTP_200_OK)
    
    def delete(self, request, variant_id):
        cart_item = CartItems.objects.get(variant_id = variant_id)

        cart_item.delete()
        return Response({'message': 'Item removed from cart'}, status = status.HTTP_200_OK)



        
class Checkout(APIView):
    permission_classes = [IsAuthenticatedAndNotBlocked]

    @transaction.atomic
    def post(self, request):
        try:
            user = request.user
            customer = request.user.customer_profile

            data =request.data
            items_data = data.get('items', [])
            if not items_data:
                return Response({'error':'No items in cart'}, status=status.HTTP_400_BAD_REQUEST)

            order = Order.objects.create(customer = customer, total_price = Decimal('0.0'))

            total_price = Decimal('0.00')
            for item in items_data:
                try:
                    variant = ProductVariants.objects.get(id = item['variant_id'])
                    quantity = int(item['quantity'])
                    order_item = OrderItems.objects.create(order = order, variant = variant, quantity = quantity)
                    print(type(variant.stock))
                    print(type(quantity))
                    variant.stock -= quantity
                    variant.save()
                    print(type(total_price))
                    print(type(order_item.price))
                    total_price += order_item.price
                except ProductVariants.DoesNotExist:
                    return Response({'error':'Product not found'}, status=status.HTTP_404_NOT_FOUND)
            
            order.total_price = Decimal(total_price)
            order.save()

            address_id = data.get('address_id') 
            address = CustomerAddress.objects.get(id = address_id, customer = customer)
            address_data = model_to_dict(address, exclude = ['id','customer'])
            ShippingAddress.objects.create(order = order, customer = customer,name = f"{customer.first_name} {customer.last_name}", phone_number = customer.phone_number, **address_data)

            payment_mode= data.get('payment_mode')

            if payment_mode == 'cash_on_delivery':
                payment = Payments.objects.create(order = order, payment_method = 'cod')

                try:
                    cart = Cart.objects.get(user = user)
                    cart.items.all().delete()
                    cart.total_price = Decimal('0.00')
                    cart.save()
                except Cart.DoesNotExist:
                    pass

                return Response({'success': True, 'message': "Order placed successfully with Cash on Delivery", 'order_id': order.id, 'total_amount': order.final_price}, status=status.HTTP_200_OK)
            

        
        except Exception as e:
            print(f"error processing checkout: ", {str(e)})
            return Response({'error': 'Failed to process order'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    def get(self, request):
        customer = request.user.customer_profile
        orders = customer.customer_order_details.all()

        response_data = []

        for order in orders:    
            shipping_address = ShippingAddress.objects.get(customer = customer, order = order)
            payment_details = Payments.objects.get(order = order)
            order_items = OrderItems.objects.filter(order = order)

            response_data_per_order = {
                'order_id': order.id,
                'shipping_address': {
                    'name': f"{customer.first_name} {customer.last_name}",
                    'phone_number':customer.phone_number,
                    'street_address':shipping_address.street_address,
                    'city':shipping_address.city,
                    'state':shipping_address.state,
                    'country':shipping_address.country,
                    'pincode': shipping_address.pincode,
                },
                'order_items': [{
                    'name':order_item.variant.product.name,
                    'brand': order_item.variant.product.vendor.company_name,
                    'variant':f"{order_item.variant.variant_unit} {order_item.variant.quantity}",
                    'product_image_url':request.build_absolute_uri(order_item.variant.product.product_images.first().image.url),
                    'quantity':order_item.quantity,
                    'price': order_item.price,
                    'order_item_status':order_item.order_item_status,
                } for order_item in order_items],
                'subtotal':order.total_price,
                'discount':order.discount_price,
                'final_price':order.final_price,
                'order_creation_time':order.created_at.strftime("%Y-%m-%d %H:%M"),
                'order_status': order.order_status,
                'payment_details':{
                    'payment_status':payment_details.payment_status,
                    'payment_method': payment_details.payment_method,
                    'transaction_id':payment_details.transaction_id if payment_details else None,   
                }
                
            }

            response_data.append(response_data_per_order)
        

        return Response(response_data, status=status.HTTP_200_OK)


        
        


