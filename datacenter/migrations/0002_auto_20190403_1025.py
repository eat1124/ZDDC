# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2019-04-03 10:25
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('datacenter', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='target',
            name='adminapp',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='target_adminapp_set', to='datacenter.App'),
        ),
    ]
