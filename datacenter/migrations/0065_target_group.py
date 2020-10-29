# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2020-10-29 09:43
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('datacenter', '0064_electricenergy'),
    ]

    operations = [
        migrations.AddField(
            model_name='target',
            name='group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='datacenter.Group', verbose_name='权限组'),
        ),
    ]
