import razorpay
from wallet.models import Wallet, WalletTransactionCustomer, WalletTransactionsAdmin
from django.conf import settings
from django.forms.models import model_to_dict
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from authentication.permissions import IsAuthenticatedAndNotBlocked, IsCustomer
from .models import Cart, CartItems
from vendor_side.models import ProductVariants
from authentication.models import CustomerAddress
from rest_framework.response import Response
from rest_framework import status
from .models import *
from django.db import transaction
from decimal import Decimal
from authentication.permissions import IsAdmin
from admin_side.models import Coupon, UsedCoupon
from django.contrib.auth import get_user_model
# Create your views here.

import logging
from razorpay.errors import BadRequestError

logger = logging.getLogger(__name__)
User = get_user_model()

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



#This view accepts the post data from the cart to create an order for the customer and also clearing the cart as a sideeffect.
#Also gets the order details of each customer to showcase on their my orders tab.


client = razorpay.Client(auth = (settings.RAZORPAY_KEY_ID,settings.RAZORPAY_KEY_SECRET))

class Checkout(APIView):
    permission_classes = [IsAuthenticatedAndNotBlocked]

    @transaction.atomic
    def post(self, request):
        try:
            user = request.user
            customer = request.user.customer_profile
            coupon_id = request.data.get('coupon_id')
            data = request.data
            items_data = data.get('items', [])
            self._clear_cart(user)
            if not items_data:
                return Response({'error': 'No items in cart'}, status=status.HTTP_400_BAD_REQUEST)
            order = Order.objects.create(customer=customer, total_price=Decimal('0.0'))
            total_price = Decimal('0.00')
            
            for item in items_data:
                try:
                    variant = ProductVariants.objects.get(id=item['variant_id'])
                    quantity = int(item['quantity'])
                    if variant.stock < quantity:
                        return Response({'error': 'Insufficient stock'}, status=status.HTTP_400_BAD_REQUEST)
                    
                    order_item = OrderItems.objects.create(order=order, variant=variant, quantity=quantity)
                    variant.stock -= quantity
                    variant.save()
                    total_price += order_item.price
                except ProductVariants.DoesNotExist:
                    return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

            # Apply coupon if valid
            discount = Decimal('0.00')
            if coupon_id:
                try:
                    coupon = Coupon.objects.get(id=coupon_id)
                    if UsedCoupon.objects.filter(user=user, coupon=coupon).exists():
                        return Response({'error': 'Coupon already used'}, status=status.HTTP_400_BAD_REQUEST)
                    
                    if total_price >= coupon.min_order_value:
                        if coupon.discount_type == 'percentage':
                            discount = total_price * coupon.discount_value / 100
                            if discount > coupon.max_discount:
                                discount = coupon.max_discount
                        else:
                            discount = coupon.discount_value
                        
                        UsedCoupon.objects.create(user=user, coupon=coupon)
                except Coupon.DoesNotExist:
                    return Response({'error': 'Invalid Coupon'}, status=status.HTTP_400_BAD_REQUEST)

            order.total_price = total_price
            order.discount_price = discount
            order.coupon = coupon if coupon_id else None
            order.save()

            # Add shipping address
            address_id = data.get('address_id')
            address = CustomerAddress.objects.get(id=address_id, customer=customer)
            address_data = model_to_dict(address, exclude=['id', 'customer'])
            ShippingAddress.objects.create(order=order, customer=customer, name=f"{customer.first_name} {customer.last_name}", phone_number=customer.phone_number, **address_data)

            # Handle payment
            payment_mode = data.get('payment_mode')
            if payment_mode == 'cash_on_delivery':
                Payments.objects.create(order=order, payment_method='cod')
                return Response({'success': True, 'message': "Order placed successfully with Cash on Delivery", 'order_id': order.id, 'total_amount': order.final_price}, status=status.HTTP_200_OK)
            
            elif payment_mode == 'card':
                try:
                    razorpay_order = client.order.create({
                        'amount': int(order.final_price * 100),
                        'currency': 'INR',
                        'payment_capture': 1
                    })
                    Payments.objects.create(
                        order=order,
                        payment_method='card',
                        payment_status='pending',
                        transaction_id=razorpay_order['id']
                    )
                    return Response({
                        'success': True,
                        'message': 'Razorpay order created',
                        'order_id': order.id,
                        'razorpay_order_id': razorpay_order['id'],
                        'amount': razorpay_order['amount'],
                        'currency': razorpay_order['currency'],
                        'key': settings.RAZORPAY_KEY_ID,
                    }, status=status.HTTP_200_OK)
                except BadRequestError as e:
                    logger.error(f"Razorpay API error: {str(e)}")
                    return Response({'error': 'Failed to create Razorpay order'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            elif payment_mode == 'wallet':
                try:
                    Payments.objects.create(order = order, payment_method = payment_mode, payment_status = 'completed') 
                    wallet = Wallet.objects.get(user = user)
                    wallet.debit(amount = order.final_price)
                    wallet_transaction = WalletTransactionCustomer.objects.create(user = user, amount = order.final_price, transaction_type = 'debit')
                    admin = User.objects.get(role = 'admin')
                    admin_wallet, created = Wallet.objects.get_or_create(user = admin)
                    admin_wallet.credit(amount = order.final_price)
                    admin_wallet_transaction = WalletTransactionsAdmin.objects.create(user = admin, amount = order.final_price, transaction_type = 'credit', transaction_through = 'wallet', transacted_user = user)
                except BadRequestError as e:
                    logger.error(f"error: {str(e)}")
                    return Response({'error': 'Failed to carry out the payment'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                return Response({
                    'success': True,
                    'message': 'Order placed successfully with wallet',
                    'order_id': order.id,
                    'total_amount': order.final_price
                    }, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid payment mode'}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error processing checkout: {str(e)}")
            return Response({'error': 'Failed to process order'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _clear_cart(self, user):
        try:
            cart = Cart.objects.get(user=user)
            cart.items.all().delete()
            cart.total_price = Decimal('0.00')
            cart.save()
        except Cart.DoesNotExist:
            pass
    def get(self, request):
        customer = request.user.customer_profile
        orders = customer.customer_order_details.order_by('-created_at')

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
                    'id': order_item.id,
                    'name':order_item.variant.product.name,
                    'brand': order_item.variant.product.vendor.company_name,
                    'variant':f"{order_item.variant.variant_unit} {order_item.variant.quantity}",
                    'product_image_url':request.build_absolute_uri(order_item.variant.product.product_images.first().image.url),
                    'quantity':order_item.quantity,
                    'price': order_item.price,
                    'order_item_status':order_item.get_order_item_status_display(),
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



class RazorpayCallback(APIView):
    def post(self, request):
        try:
            user = request.user
            data = request.data
            razorpay_order_id = data.get('razorpay_order_id')
            razorpay_payment_id = data.get('razorpay_payment_id')
            razorpay_signature = data.get('razorpay_signature')

            logger.info(f"Razorpay callback received: {data}")

            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }

            # Verify payment signature
            try:
                client.utility.verify_payment_signature(params_dict)
                logger.info("Payment signature verified successfully")
            except razorpay.errors.SignatureVerificationError as e:
                logger.error(f"Invalid payment signature: {str(e)}")
                return Response({'error': 'Invalid payment signature'}, status=status.HTTP_400_BAD_REQUEST)

            # Update payment status
            with transaction.atomic():
                try:
                    payment = Payments.objects.select_for_update().get(transaction_id=razorpay_order_id)
                    payment.transaction_id = razorpay_payment_id
                    payment.payment_status = 'completed'
                    payment.save()
                    order = payment.order
                    admin = User.objects.get(role = 'admin')
                    admin_wallet, created = Wallet.objects.get_or_create(user = admin)
                    admin_wallet.credit(order.final_price)
                    admin_wallet_transaction = WalletTransactionsAdmin.objects.create(user = admin, transacted_user = user, transaction_through = 'card', amount = order.final_price, transaction_type = 'credit')
                    logger.info(f"Payment status updated to 'completed' for order: {razorpay_order_id}")
                except Payments.DoesNotExist:
                    logger.error(f"Payment not found for order: {razorpay_order_id}")
                    return Response({'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)
                except Exception as e:
                    logger.error(f"Error updating payment status: {str(e)}")
                    raise

            return Response({'success': True, 'message': 'Payment successful'}, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error processing Razorpay callback: {str(e)}")
            return Response({'error': 'Failed to process payment'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsCustomer])
def retry_payment(request):
    order_id = request.data.get('order_id')
    try:
        order = Order.objects.get(id = order_id)
        razorpay_order = client.order.create({
            'amount': int(order.final_price*100),
            'currency': 'INR',
            'payment_capture': 1
        })

        payment = Payments.objects.get(order_id = order_id)
        payment.transaction_id = razorpay_order['id']
        payment.save()

        user = request.user
        admin = User.objects.get(role = 'admin')
        admin_wallet, created = Wallet.objects.get_or_create(user = admin)
        admin_wallet.credit(order.final_price)
        admin_wallet_transaction = WalletTransactionsAdmin.objects.create(user = admin, transacted_user = user, transaction_through = 'card', amount = order.final_price, transaction_type = 'credit')

        return Response({
            'success': True,
            'message': 'Razorpay order created',
            'order_id': order.id,
            'razorpay_order_id': razorpay_order['id'],
            'amount': razorpay_order['amount'],
            'currency': razorpay_order['currency'],
            'key': settings.RAZORPAY_KEY_ID,
        }, status=status.HTTP_200_OK)
    except Order.DoesNotExist():
        return Response({'error': 'order not found'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        # Log the error for debugging
        print(f"Error in retry_payment: {str(e)}")
        return Response({'error': 'An error occurred while processing your request'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

