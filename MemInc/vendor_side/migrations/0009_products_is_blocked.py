# Generated by Django 5.1.5 on 2025-04-08 05:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendor_side', '0008_rename_is_created_products_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='products',
            name='is_blocked',
            field=models.BooleanField(default=False),
        ),
    ]
