# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2019-04-11 12:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datacenter', '0008_calculatedata_calculateguid'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='calculatedata',
            name='calculateguid',
        ),
        migrations.AddField(
            model_name='target',
            name='calculateguid',
            field=models.CharField(max_length=50, null=True, verbose_name='计算GUID'),
        ),
    ]
