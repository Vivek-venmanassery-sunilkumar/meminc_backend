# Generated by Django 5.1.5 on 2025-02-16 11:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0007_customuser_is_staff_alter_customuser_role'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='profile_picture',
            field=models.ImageField(blank=True, null=True, upload_to='profile_pictures/customers/'),
        ),
        migrations.AlterField(
            model_name='vendor',
            name='profile_picture',
            field=models.ImageField(blank=True, null=True, upload_to='profile_pictures/vendors/'),
        ),
    ]
