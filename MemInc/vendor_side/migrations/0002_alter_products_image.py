# Generated by Django 5.1.5 on 2025-02-12 07:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendor_side', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='products',
            name='image',
            field=models.ImageField(upload_to='products/'),
        ),
    ]
