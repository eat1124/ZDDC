# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2020-02-11 11:11
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('datacenter', '0023_auto_20200210_2303'),
    ]

    operations = [
        migrations.RenameField(
            model_name='meterchangedata',
            old_name='nwetable_value',
            new_name='newtable_value',
        ),
    ]
