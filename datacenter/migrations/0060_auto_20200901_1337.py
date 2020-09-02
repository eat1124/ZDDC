# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2020-09-01 13:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datacenter', '0059_auto_20200810_1047'),
    ]

    operations = [
        migrations.AddField(
            model_name='userinfo',
            name='ad_user',
            field=models.CharField(default='', max_length=128, null=True, verbose_name='AD域 用户'),
        ),
        migrations.AddField(
            model_name='userinfo',
            name='if_ad_login',
            field=models.IntegerField(choices=[(0, '否'), (1, '是')], default=0, null=True, verbose_name='是否可通过域用户登录'),
        ),
    ]