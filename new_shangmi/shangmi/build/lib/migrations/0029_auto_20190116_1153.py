# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-01-16 11:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shangmi', '0028_auto_20190109_1546'),
    ]

    operations = [
        migrations.AddField(
            model_name='shangmiuser',
            name='idcard',
            field=models.CharField(max_length=20, null=True, verbose_name='身份证'),
        ),
        migrations.AddField(
            model_name='shangmiuser',
            name='name',
            field=models.CharField(max_length=30, null=True, verbose_name='用户姓名'),
        ),
        migrations.AddField(
            model_name='shangmiuser',
            name='phone',
            field=models.CharField(max_length=20, null=True, verbose_name='手机号'),
        ),
    ]
