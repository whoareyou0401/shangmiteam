# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-04-06 22:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shangmi', '0041_auto_20190404_1756'),
    ]

    operations = [
        migrations.AddField(
            model_name='store',
            name='get_money_phone',
            field=models.CharField(max_length=16, null=True, verbose_name='提现老板手机号'),
        ),
        migrations.AlterField(
            model_name='store',
            name='balance',
            field=models.IntegerField(default=0, verbose_name='门店余额(分)'),
        ),
    ]