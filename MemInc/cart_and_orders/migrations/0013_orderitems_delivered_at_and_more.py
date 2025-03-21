# Generated by Django 5.1.5 on 2025-03-21 11:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cart_and_orders', '0012_wishlist_wishlistitems'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitems',
            name='delivered_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='orderitems',
            name='is_payment_done_to_vendor',
            field=models.BooleanField(default=False),
        ),
    ]
