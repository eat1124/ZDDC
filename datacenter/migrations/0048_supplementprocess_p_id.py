# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2020-04-09 15:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datacenter', '0047_supplementprocess'),
    ]

    operations = [
        migrations.AddField(
            model_name='supplementprocess',
            name='p_id',
            field=models.CharField(blank=True, default='', max_length=50, verbose_name='进程ID'),
        ),
    ]
