# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2020-02-10 12:56
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('datacenter', '0025_auto_20200210_1239'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cycle',
            name='code',
        ),
    ]