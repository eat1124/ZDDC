# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2020-02-10 12:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datacenter', '0023_meterdata'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cycle',
            name='creatdate',
        ),
        migrations.RemoveField(
            model_name='cycle',
            name='minutes',
        ),
        migrations.AddField(
            model_name='cycle',
            name='day_of_month',
            field=models.CharField(blank=True, default='', max_length=64, verbose_name='月中日'),
        ),
        migrations.AddField(
            model_name='cycle',
            name='day_of_week',
            field=models.CharField(blank=True, default='', max_length=64, verbose_name='周中日'),
        ),
        migrations.AddField(
            model_name='cycle',
            name='hour',
            field=models.CharField(blank=True, default='', max_length=64, verbose_name='小时'),
        ),
        migrations.AddField(
            model_name='cycle',
            name='minute',
            field=models.CharField(blank=True, default='', max_length=64, verbose_name='分钟'),
        ),
    ]
