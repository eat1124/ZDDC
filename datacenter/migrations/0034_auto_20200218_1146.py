# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2020-02-18 11:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datacenter', '0033_auto_20200217_1210'),
    ]

    operations = [
        migrations.AlterField(
            model_name='source',
            name='type',
            field=models.CharField(blank=True, default='', max_length=20, verbose_name='类型：动态类型为空字符串，固定类型(数据补取：1，数据清理：2，数据服务：3，短信服务：4)'),
        ),
    ]