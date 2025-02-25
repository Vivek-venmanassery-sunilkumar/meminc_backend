
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from authentication.permissions import IsAuthenticatedAndNotBlocked, IsCustomer
from .models import Cart, CartItems
from vendor_side.models import Products, ProductImages, ProductVariants
from authentication.models import Vendor
from rest_framework.response import Response
from rest_framework import status
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

        quantity =int(request.data.get('quantity', 1))

        if quantity <= 0:
            return Response({'error':'Quantity must be greater than 0'}, status=status.HTTP_400_BAD_REQUEST)

        cart_item, created = CartItems.objects.create(cart = cart, variant = variant)
        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
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



        
