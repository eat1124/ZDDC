# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2021-04-01 11:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datacenter', '0079_targetstatistic_sort'),
    ]

    operations = [
        migrations.AlterField(
            model_name='target',
            name='cumulative',
            field=models.CharField(choices=[('0', '不累计'), ('1', '求和'), ('2', '算术平均'), ('3', '加权平均'), ('4', '非零算术平均'), ('5', '求和(上月)(环保专用)')], max_length=20, null=True, verbose_name='累计类型'),
        ),
    ]
