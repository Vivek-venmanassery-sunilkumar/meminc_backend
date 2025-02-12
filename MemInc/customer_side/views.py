from rest_framework.response import Response
from rest_framework import status
from vendor_side.models import Products
from rest_framework.decorators import api_view
from admin_side.views import custom_pagination


# Create your views here.


@api_view(['GET'])
def product_listing_customer_side(request):
    products = Products.objects.all()

    product_data = []
    for product in products:
        image_url = request.build_absolute_uri(product.image.url) if product.image else None
        variants = product.variant_profile.all()
        variant_data = []
        for variant in variants:
            variant_data.append({
                'id': variant.id,
                'name': f'{variant.quantity} {product.variant_unit}',
                'price': variant.price,
                'stock': variant.stock
            })
        product_data.append({
            'product_name':product.name,
            'product_image':image_url,
            'category': product.category.category,
            'company_name': product.vendor.company_name,
            'variants': variant_data
        })


    paginator = custom_pagination()
    paginated_products = paginator.paginate_queryset(product_data, request)

    if paginated_products is not None:
        return paginator.get_paginated_response(paginated_products)
    return Response([])