# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2020-03-13 10:48
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datacenter', '0039_fun_work'),
    ]

    operations = [
        migrations.AddField(
            model_name='target',
            name='unity',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='单位'),
        ),
    ]
