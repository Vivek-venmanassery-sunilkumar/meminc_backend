from django.apps import AppConfig


class CartAndOrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cart_and_orders'

    def ready(self):
        from .scheduler import start_scheduler_for_vendor_payment_update

        start_scheduler_for_vendor_payment_update()