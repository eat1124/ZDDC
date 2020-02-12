# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2020-02-10 23:03
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('datacenter', '0022_auto_20200113_1556'),
    ]

    operations = [
        migrations.CreateModel(
            name='Meterchangedata',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datadate', models.DateTimeField(blank=True, null=True, verbose_name='开始时间')),
                ('oldtable_zerodata', models.DecimalField(decimal_places=5, max_digits=20, null=True, verbose_name='旧表起始走字')),
                ('oldtable_twentyfourdata', models.DecimalField(decimal_places=5, max_digits=20, null=True, verbose_name='旧表最终走字')),
                ('oldtable_value', models.DecimalField(decimal_places=5, max_digits=20, null=True, verbose_name='旧表差值')),
                ('oldtable_magnification', models.DecimalField(decimal_places=5, max_digits=18, null=True, verbose_name='旧表倍率')),
                ('oldtable_finalvalue', models.DecimalField(decimal_places=5, max_digits=20, null=True, verbose_name='旧表最终值')),
                ('newtable_zerodata', models.DecimalField(decimal_places=5, max_digits=20, null=True, verbose_name='新表起始走字')),
                ('newtable_twentyfourdata', models.DecimalField(decimal_places=5, max_digits=20, null=True, verbose_name='新表最终走字')),
                ('nwetable_value', models.DecimalField(decimal_places=5, max_digits=20, null=True, verbose_name='新表差值')),
                ('newtable_magnification', models.DecimalField(decimal_places=5, max_digits=18, null=True, verbose_name='新表倍率')),
                ('newtable_finalvalue', models.DecimalField(decimal_places=5, max_digits=20, null=True, verbose_name='新表最终值')),
                ('finalvalue', models.DecimalField(decimal_places=5, max_digits=20, null=True, verbose_name='最终计算值')),
                ('state', models.CharField(blank=True, max_length=20, null=True, verbose_name='状态')),
            ],
        ),
        migrations.CreateModel(
            name='Meterdata',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datadate', models.DateTimeField(blank=True, null=True, verbose_name='开始时间')),
                ('zerodata', models.CharField(max_length=20, null=True, verbose_name='零点走字')),
                ('twentyfourdata', models.CharField(max_length=20, null=True, verbose_name='二十四点走字')),
                ('metervalue', models.CharField(max_length=20, null=True, verbose_name='电表数值')),
                ('curvalue', models.DecimalField(decimal_places=5, max_digits=20, null=True, verbose_name='当前值')),
                ('curvaluedate', models.DateTimeField(null=True, verbose_name='当前值')),
                ('curvaluetext', models.CharField(max_length=20, null=True, verbose_name='当前值')),
                ('cumulativemonth', models.DecimalField(decimal_places=5, max_digits=20, null=True, verbose_name='月累计值')),
                ('cumulativequarter', models.DecimalField(decimal_places=5, max_digits=20, null=True, verbose_name='季累计值')),
                ('cumulativehalfyear', models.DecimalField(decimal_places=5, max_digits=20, null=True, verbose_name='半年累计值')),
                ('cumulativeyear', models.DecimalField(decimal_places=5, max_digits=20, null=True, verbose_name='年累计值')),
                ('state', models.CharField(blank=True, max_length=20, null=True, verbose_name='状态')),
                ('target', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='datacenter.Target')),
            ],
        ),
        migrations.AddField(
            model_name='meterchangedata',
            name='meterdata',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='datacenter.Meterdata'),
        ),
    ]
