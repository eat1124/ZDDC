# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2020-10-29 11:48
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('datacenter', '0066_auto_20201029_1142'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='targetstatistic',
            name='group',
        ),
    ]
