# Generated by Django 5.1.5 on 2025-02-20 05:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0009_alter_customer_phone_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='profile_picture_url',
            field=models.URLField(blank=True),
        ),
    ]
