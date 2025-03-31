from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from .models import Coupon, Banner
from django.utils.timezone import now

def update_coupon_status():
    
    current_date = now().date()  # Extract only the date part

    print(f"Current date: {current_date}")

    updated_active = Coupon.objects.filter(start_date__lte =current_date, expiry_date__gte = current_date).update(is_active = True)
    updated_inactive = Coupon.objects.filter(expiry_date__lt = current_date).update(is_active = False)


    print(f"Updated {updated_active} active coupons and {updated_inactive} inactive coupons.")
    print("Successfully updated coupon statuses.")

def update_banner_status():
    
    current_date = now().date()

    update_active = Banner.objects.filter(start_date__lte = current_date, expiry_date__gte = current_date).update(is_active = True)
    update_inactive = Banner.objects.filter(expiry_date__lt = current_date).update(is_active = False)

    print(f"Updated {update_active} active coupons and {update_inactive} inactive coupons.")
    print("Successfully updated coupon statuses.")

def run_missed_job():
    update_coupon_status()
    update_banner_status()
    print("Ran updated_coupon_status() on server startup")

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

    scheduler.add_job(
        update_banner_status,
        'cron',
        hour = 0,
        minute = 0,
        id = 'update_banner_status',
        replace_existing=True
    )

    scheduler.start()
    print("Scheduler started successfully.")
    print(f"Scheduled jobs: {scheduler.get_jobs()}")

    run_missed_job()


