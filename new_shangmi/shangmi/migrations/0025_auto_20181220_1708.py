# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-12-20 17:08
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shangmi', '0024_auto_20181220_1131'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='userrecharge',
            options={'verbose_name': '门店用户充值'},
        ),
        migrations.AddField(
            model_name='shangmiuser',
            name='lat',
            field=models.DecimalField(decimal_places=15, max_digits=30, null=True, verbose_name='纬度'),
        ),
        migrations.AddField(
            model_name='shangmiuser',
            name='lng',
            field=models.DecimalField(decimal_places=15, max_digits=30, null=True, verbose_name='经度'),
        ),
        migrations.AlterField(
            model_name='storeactivebalance',
            name='store',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='shangmi.Store', verbose_name='门店'),
        ),
    ]
