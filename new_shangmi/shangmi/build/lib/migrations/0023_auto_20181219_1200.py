# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-12-19 12:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shangmi', '0022_userpaylog_prepay_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='shangmiuser',
            name='gz_openid',
            field=models.CharField(max_length=255, null=True, verbose_name='公众号openid'),
        ),
        migrations.AddField(
            model_name='shangmiuser',
            name='union_id',
            field=models.CharField(max_length=255, null=True, verbose_name='联合主键'),
        ),
    ]
