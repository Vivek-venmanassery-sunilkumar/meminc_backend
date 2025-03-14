import razorpay
from django.db import transaction
from rest_framework.decorators import api_view,permission_classes
from authentication.permissions import IsAuthenticatedAndNotBlocked, IsCustomer
from decimal import Decimal
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import logging
from .models import Wallet, WalletTransactionCustomer
# Create your views here.



logging.basicConfig(level=logging.INFO)  # Set log level to INFO
logger = logging.getLogger(__name__)


client =razorpay.Client(auth = (settings.RAZORPAY_KEY_ID,settings.RAZORPAY_KEY_SECRET))

@api_view(['POST'])
@permission_classes([IsAuthenticatedAndNotBlocked])
def customer_wallet_credit(request):
    amount = request.data['amount']

    if not Decimal(amount) >  Decimal(500):
        return Response({'error': 'Invalid amount'}, status= status.HTTP_400_BAD_REQUEST)
    
    razorpay_order = client.order.create({
        'amount': int(amount)*100,
        'currency': 'INR',
        'payment_capture': 1,
    })

    return Response({
        'success': True,
        'message': 'Razorpay order created',
        'key': settings.RAZORPAY_KEY_ID,
        'order_id':razorpay_order['id']
    },status=status.HTTP_200_OK) 


@api_view(['POST'])
@permission_classes([IsAuthenticatedAndNotBlocked])
def customer_wallet_credit_callback(request): 
    user = request.user
    data = request.data
    razorpay_order_id = data.get('razorpay_order_id')
    razorpay_payment_id = data.get('razorpay_payment_id')
    razorpay_signature = data.get('razorpay_signature')
    amount = data.get('amount')
    logger.info(f'wallet razorpay callback recieved: {data}')

    params_dict = {
        'razorpay_order_id':razorpay_order_id,
        'razorpay_payment_id': razorpay_payment_id,
        'razorpay_signature': razorpay_signature
    }


    try:
        client.utility.verify_payment_signature(params_dict)
        logger.info("Payment signature verified successfully")
    except razorpay.errors.SignatureVerificationError as e:
        logger.error(f"Invalid payment signature: {str(e)}")
        return Response({"error": "Invalid payment signature"}, status=status.HTTP_400_BAD_REQUEST)
    
    
    with transaction.atomic():
        wallet,created = Wallet.objects.get_or_create(user = user)
        wallet.credit(amount)

        wallet_transaction = WalletTransactionCustomer.objects.create(
            user = user,
            transaction_type = 'credit', 
            amount = Decimal(amount),
            transaction_id = razorpay_payment_id
        )

        return Response({'success': True, 'wallet_balance': wallet.balance}, status=status.HTTP_200_OK)
    

@api_view(['GET'])
@permission_classes([IsCustomer])
def customer_wallet_balance_fetch(request):
    user = request.user
    try:
        wallet = Wallet.objects.get(user = user)
    except Wallet.DoesNotExist:
        return Response({'error': 'The wallet balance is zero'}, status=status.HTTP_404_NOT_FOUND)

    return Response({'wallet_balance': wallet.balance}, status=status.HTTP_200_OK)