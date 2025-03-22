import razorpay
from django.db import transaction
from rest_framework.decorators import api_view,permission_classes
from authentication.permissions import IsAuthenticatedAndNotBlocked, IsCustomer, IsAdmin, IsVendor
from decimal import Decimal
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import logging
from .models import Wallet, WalletTransactionCustomer, WalletTransactionsAdmin, WalletTransactionsVendor
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
    wallet,created = Wallet.objects.get_or_create(user = user)

    return Response({'wallet_balance': wallet.balance}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAdmin])
def admin_wallet_balance_fetch(request):
    user = request.user
    wallet, created = Wallet.objects.get_or_create(user = user)
    return Response({'wallet_balance': wallet.balance},status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsVendor])
def vendor_wallet_balance_fetch(request):
    user = request.user
    wallet, created = Wallet.objects.get_or_create(user = user)
    return Response({'wallet_balance': wallet.balance},status = status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAdmin])
def admin_wallet_transactions_fetch(request):
    user = request.user
    try:
        wallet_transactions = WalletTransactionsAdmin.objects.all().order_by('-timestamp')
        transactions = []
        for wallet_transaction in wallet_transactions:
            transaction = {
                'transacted_user': wallet_transaction.transacted_user.email,
                'transaction_type': wallet_transaction.transaction_type,
                'transaction_through': wallet_transaction.transaction_through,
                'amount': wallet_transaction.amount,
                'timestamp': wallet_transaction.timestamp,
            }
            transactions.append(transaction)
    except WalletTransactionsAdmin.DoesNotExist:
        return Response({'error': 'No transactions till now'}, status=status.HTTP_404_NOT_FOUND) 
    return Response(transactions,status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsVendor])
def vendor_wallet_transactions_fetch(request):
    user = request.user
    try:
        wallet_transactions = WalletTransactionsVendor.objects.filter(user = user).order_by('-timestamp')
        transactions = []
        for wallet_transaction in wallet_transactions:
            transaction = {
                'transaction_for': f'Payment for {wallet_transaction.order_item.variant.product.name} {wallet_transaction.order_item.variant.quantity} {wallet_transaction.order_item.variant.variant_unit} of {wallet_transaction.order_item.quantity} items',
                'transaction_type': wallet_transaction.transaction_type,
                'transaction_through': wallet_transaction.transaction_through,
                'amount': wallet_transaction.amount,
                'timestamp': wallet_transaction.timestamp
            }
            transactions.append(transaction)
    except WalletTransactionsVendor.DoesNotExist:
        return Response({'error':'No transactions till now'}, status=status.HTTP_404_NOT_FOUND)
    return Response(transactions, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsCustomer])
def customer_wallet_transactons_fetch(request):
    user = request.user
    try:
        wallet_transactions = WalletTransactionCustomer.objects.filter(user = user).order_by('-timestamp')
        transactions = []
        for wallet_transaction in wallet_transactions:
            transaction = {
                'transaction_id': wallet_transaction.transaction_id,
                'transaction_type': wallet_transaction.transaction_type,
                'amount': wallet_transaction.amount,
                'timestamp': wallet_transaction.timestamp,
            }
            transactions.append(transaction)
    except WalletTransactionCustomer.DoesNotExist:
        return Response({'error': 'No transactions till now'}, status=status.HTTP_404_NOT_FOUND)
    return Response(transactions, status=status.HTTP_200_OK)