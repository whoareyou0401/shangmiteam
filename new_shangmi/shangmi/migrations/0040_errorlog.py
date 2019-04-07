# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2019-03-06 22:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shangmi', '0039_auto_20190301_2111'),
    ]

    operations = [
        migrations.CreateModel(
            name='ErrorLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('msg', models.CharField(max_length=255, verbose_name='错误信息')),
                ('api_path', models.CharField(max_length=255, verbose_name='请求路径')),
                ('date', models.DateField(auto_now_add=True, verbose_name='错误发送时间')),
            ],
        ),
    ]
