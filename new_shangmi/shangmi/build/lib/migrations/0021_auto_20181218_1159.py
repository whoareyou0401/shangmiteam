# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-12-18 11:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shangmi', '0020_remove_storeactivebalance_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='active',
            name='lat',
            field=models.DecimalField(decimal_places=15, max_digits=30, null=True, verbose_name='纬度'),
        ),
        migrations.AddField(
            model_name='active',
            name='lng',
            field=models.DecimalField(decimal_places=15, max_digits=30, null=True, verbose_name='经度'),
        ),
        migrations.AddField(
            model_name='active',
            name='range',
            field=models.FloatField(default=3, verbose_name='活动允许范围km'),
        ),
    ]
