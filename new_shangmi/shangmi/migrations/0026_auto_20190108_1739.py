# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-01-08 17:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shangmi', '0025_auto_20181220_1708'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='store',
            options={'verbose_name': '门店'},
        ),
        migrations.AddField(
            model_name='store',
            name='is_recive',
            field=models.BooleanField(default=True, verbose_name='语音通知状态'),
        ),
    ]
