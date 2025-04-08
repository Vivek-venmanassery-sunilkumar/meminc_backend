from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from .models import OrderItems, Order
from django.contrib.auth import get_user_model
from wallet.models import Wallet, WalletTransactionsAdmin, WalletTransactionsVendor, CommissionRecievedAdminPerOrder
from datetime import timedelta
from django.utils.timezone import now
from decimal import Decimal
from django.db import transaction
User = get_user_model()


def vendor_payment_update():
    current_date_time = now()
    print('Inside vendor payment update')

    order_items = OrderItems.objects.all()
    
    admin = User.objects.get(role = 'admin')


    with transaction.atomic():
        for order_item in order_items:
            if order_item.is_payment_done_to_vendor:
                continue
            deliver_date_time = order_item.delivered_at 
            if not deliver_date_time:
                continue
            time_difference = current_date_time - deliver_date_time

            if time_difference >= timedelta(minutes = 1):

                vendor = order_item.variant.product.vendor.user

                vendor_wallet,created = Wallet.objects.get_or_create(user = vendor)
                vendor_credit_amount = order_item.price * 80 / 100

                vendor_wallet.credit(vendor_credit_amount)

                WalletTransactionsVendor.objects.create(
                    user = vendor,
                    order_item = order_item,
                    amount = vendor_credit_amount,
                    transaction_type = 'credit',
                    transaction_through = 'wallet',
                    transacted_user = admin
                )

                admin_wallet,created = Wallet.objects.get_or_create(user = admin)
                admin_wallet.debit(vendor_credit_amount)
                
                WalletTransactionsAdmin.objects.create(
                    user = admin,
                    amount = vendor_credit_amount,
                    transaction_type = 'debit',
                    transaction_through = 'wallet',
                    transacted_user = vendor,
                )
                order_item.is_payment_done_to_vendor = True
                order_item.payment_done_to_vendor = Decimal(vendor_credit_amount)
                order_item.save()
                print('all work done')
        

    orders = Order.objects.all()

    for order in orders:
        if order.are_all_payments_done_to_vendor():
            if CommissionRecievedAdminPerOrder.objects.filter(order = order).exists():
                continue

            order_items = OrderItems.objects.filter(order = order)
            payment_done_to_vendor_total = 0
            for order_item in order_items:
                if order_item.order_item_status != 'cancelled':
                    payment_done_to_vendor_total += order_item.payment_done_to_vendor
            
            commission_needed_to_be_kept = order.total_price - payment_done_to_vendor_total 

            is_discount_present = order.discount_price > 0 
            commission_kept = commission_needed_to_be_kept - order.discount_price
            CommissionRecievedAdminPerOrder.objects.create(
                user = admin,
                commission_needed_to_be_kept = commission_needed_to_be_kept,
                order = order,
                is_discount_present = is_discount_present,
                commission_kept = commission_kept,
            )

            print(f'updated the commision for admin on order_id: {order.id}')


def run_missed_job_vendor_payment():
    vendor_payment_update()
    print("Ran the vendor payment update successfully")

def start_scheduler_for_vendor_payment_update():
    scheduler = BackgroundScheduler()

    scheduler.add_jobstore(DjangoJobStore(), 'default')

    scheduler.add_job(
        vendor_payment_update,
        'interval',
        minutes = 1,
        id = 'vendor_payment_update',
        replace_existing=True
    )

    scheduler.start()
    print('vendor payment update scheduler started successfully')

    run_missed_job_vendor_payment()