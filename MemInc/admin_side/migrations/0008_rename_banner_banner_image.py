# Generated by Django 5.1.5 on 2025-03-28 09:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('admin_side', '0007_banner'),
    ]

    operations = [
        migrations.RenameField(
            model_name='banner',
            old_name='banner',
            new_name='image',
        ),
    ]
