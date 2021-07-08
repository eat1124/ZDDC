# -*- coding: utf-8 -*-
# Generated by Django 1.9.13 on 2021-06-18 17:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datacenter', '0081_updatedatalog'),
    ]

    operations = [
        migrations.AddField(
            model_name='updatedatalog',
            name='raw_curvalue',
            field=models.DecimalField(decimal_places=7, max_digits=22, null=True, verbose_name='原始数据'),
        ),
    ]