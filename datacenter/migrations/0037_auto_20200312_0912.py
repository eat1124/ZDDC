# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2020-03-12 09:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datacenter', '0036_work'),
    ]

    operations = [
        migrations.AlterField(
            model_name='work',
            name='core',
            field=models.CharField(blank=True, default='否', max_length=20, verbose_name='是否核心业务'),
        ),
    ]
