# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2020-04-15 11:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datacenter', '0050_auto_20200415_1101'),
    ]

    operations = [
        migrations.AlterField(
            model_name='constant',
            name='value',
            field=models.DecimalField(decimal_places=5, max_digits=20, null=True, verbose_name='常数值'),
        ),
    ]