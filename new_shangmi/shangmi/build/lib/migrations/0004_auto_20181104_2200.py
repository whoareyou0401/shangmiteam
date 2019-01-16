# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-11-04 22:00
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shangmi', '0003_active_is_fast'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserPayLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('money', models.IntegerField(verbose_name='差价钱数')),
                ('integral', models.IntegerField(verbose_name='使用的积分数')),
                ('wx_pay_num', models.CharField(max_length=255, verbose_name='微信支付订单号')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('store', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shangmi.Store', verbose_name='门店')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shangmi.ShangmiUser', verbose_name='普通用户')),
            ],
            options={
                'verbose_name': '用户付款表',
            },
        ),
        migrations.AlterIndexTogether(
            name='userpaylog',
            index_together=set([('user', 'store')]),
        ),
    ]
