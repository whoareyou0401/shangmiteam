# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-12-11 16:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shangmi', '0015_getmoneylog_partner_trade_no'),
    ]

    operations = [
        migrations.AddField(
            model_name='getmoneylog',
            name='is_ok',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='getmoneylog',
            name='payment_no',
            field=models.CharField(max_length=255, null=True),
        ),
    ]
