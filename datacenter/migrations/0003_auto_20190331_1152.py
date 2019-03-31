# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2019-03-31 11:52
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('datacenter', '0002_auto_20190325_2002'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dictlist',
            name='dictindex',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='datacenter.DictIndex'),
        ),
        migrations.AlterField(
            model_name='storage',
            name='sort',
            field=models.IntegerField(blank=True, null=True, verbose_name='排序 '),
        ),
        migrations.AlterField(
            model_name='target',
            name='cycle',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='datacenter.Cycle'),
        ),
        migrations.AlterField(
            model_name='target',
            name='source',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='datacenter.Source'),
        ),
    ]
