# -*- coding: utf-8 -*-
# Generated by Django 1.9.12 on 2020-05-12 16:53
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('datacenter', '0053_target_cumulate_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='target',
            name='cumulate_type',
        ),
        migrations.AddField(
            model_name='target',
            name='weight_target',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='datacenter.Target', verbose_name='加权指标'),
        ),
        migrations.AlterField(
            model_name='target',
            name='cumulative',
            field=models.CharField(choices=[('0', '不累计'), ('1', '求和'), ('2', '算术平均'), ('3', '加权平均')], max_length=20, null=True, verbose_name='累计类型'),
        ),
    ]