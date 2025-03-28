# Generated by Django 5.1.5 on 2025-02-27 21:54

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cart_and_orders', '0004_rename_order_id_payments_order_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='shippingaddress',
            name='name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='shippingaddress',
            name='phone_number',
            field=models.CharField(blank=True, max_length=12, null=True),
        ),
        migrations.AlterField(
            model_name='shippingaddress',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='order_shipping_address', to='cart_and_orders.order'),
        ),
    ]
