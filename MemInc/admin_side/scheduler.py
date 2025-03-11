from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from django.utils import timezone
from .models import Coupon


def update_coupon_status():
    current_date = timezone.now().date()

    Coupon.objects.filter(start_date__lte =current_date, expiry_date__gte = current_date).update(is_active = True)
    Coupon.objects.filter(expiry_date__lt = current_date).update(is_active = False)

    print("Successfully updated coupon statuses.")

def start_scheduler():
    scheduler = BackgroundScheduler()

    scheduler.add_jobstore(DjangoJobStore(), 'default')

    scheduler.add_job(
        update_coupon_status,
        'cron',
        hour = 0,
        minute = 0,
        id = 'update_coupon_status',
        replace_existing = True
    )

    scheduler.start()