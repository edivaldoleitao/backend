# Generated by Django 5.2.3 on 2025-07-27 06:27

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0029_remove_preference_build_preference_build'),
    ]

    operations = [
        migrations.AlterField(
            model_name='preference',
            name='marca',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=20), blank=True, default=list, size=None),
        ),
    ]
