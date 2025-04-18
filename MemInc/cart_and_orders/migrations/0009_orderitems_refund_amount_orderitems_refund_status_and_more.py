# Generated by Django 5.1.5 on 2025-03-15 06:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cart_and_orders', '0008_orderitems_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitems',
            name='refund_amount',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='orderitems',
            name='refund_status',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='orderitems',
            name='order_item_status',
            field=models.CharField(choices=[('processing', 'Processing'), ('dispatched', 'Dispatched'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled')], default='processing', max_length=100),
        ),
    ]
