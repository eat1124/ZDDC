# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2020-01-10 12:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datacenter', '0019_auto_20200110_1053'),
    ]

    operations = [
        migrations.AddField(
            model_name='processmonitor',
            name='last_time',
            field=models.DateTimeField(blank=True, null=True, verbose_name='最近取数时间'),
        ),
    ]
