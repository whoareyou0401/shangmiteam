# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-12-10 09:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shangmi', '0012_auto_20181209_2227'),
    ]

    operations = [
        migrations.AddField(
            model_name='userpaylog',
            name='status',
            field=models.IntegerField(choices=[(0, '待完成'), (1, '已完成')], default=0, verbose_name='支付状态'),
        ),
    ]
