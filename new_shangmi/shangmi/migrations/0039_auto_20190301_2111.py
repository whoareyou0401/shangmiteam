# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-03-01 21:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shangmi', '0038_userrecharge_recharge_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='store',
            name='is_receive',
            field=models.BooleanField(default=False, verbose_name='语音通知状态'),
        ),
        migrations.AlterField(
            model_name='userrecharge',
            name='recharge_type',
            field=models.CharField(default='账户余额', max_length=20),
        ),
    ]
