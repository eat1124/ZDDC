# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2019-04-03 10:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datacenter', '0002_auto_20190403_1025'),
    ]

    operations = [
        migrations.AlterField(
            model_name='target',
            name='cumulative',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='是否累计'),
        ),
        migrations.AlterField(
            model_name='target',
            name='formula',
            field=models.CharField(blank=True, max_length=2000, null=True, verbose_name='公式'),
        ),
        migrations.AlterField(
            model_name='target',
            name='lowerlimit',
            field=models.DecimalField(decimal_places=5, max_digits=20, null=True, verbose_name='下限'),
        ),
        migrations.AlterField(
            model_name='target',
            name='magnification',
            field=models.DecimalField(decimal_places=5, max_digits=18, null=True, verbose_name='倍率'),
        ),
        migrations.AlterField(
            model_name='target',
            name='sourceconditions',
            field=models.CharField(blank=True, max_length=2000, null=True, verbose_name='数据源条件'),
        ),
        migrations.AlterField(
            model_name='target',
            name='sourcefields',
            field=models.CharField(blank=True, max_length=2000, null=True, verbose_name='数据源字段'),
        ),
        migrations.AlterField(
            model_name='target',
            name='sourcesis',
            field=models.CharField(blank=True, max_length=2000, null=True, verbose_name='数据源sis点'),
        ),
        migrations.AlterField(
            model_name='target',
            name='sourcetable',
            field=models.CharField(blank=True, max_length=2000, null=True, verbose_name='数据源表'),
        ),
        migrations.AlterField(
            model_name='target',
            name='storagefields',
            field=models.CharField(blank=True, max_length=2000, null=True, verbose_name='存储字段'),
        ),
        migrations.AlterField(
            model_name='target',
            name='storagetag',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='存储标识'),
        ),
        migrations.AlterField(
            model_name='target',
            name='upperlimit',
            field=models.DecimalField(decimal_places=5, max_digits=20, null=True, verbose_name='上限'),
        ),
    ]