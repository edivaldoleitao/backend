# Generated by Django 5.2.3 on 2025-07-01 02:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0010_alter_product_category'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='hash',
            field=models.TextField(blank=True, editable=False, null=True, unique=True),
        ),
    ]
