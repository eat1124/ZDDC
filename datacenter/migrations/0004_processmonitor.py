# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2019-04-08 13:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datacenter', '0003_auto_20190403_1045'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProcessMonitor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=100, null=True, verbose_name='进程名称')),
                ('process_path', models.CharField(blank=True, max_length=100, null=True, verbose_name='进程路径')),
                ('create_time', models.DateTimeField(blank=True, null=True, verbose_name='进程启动时间')),
            ],
        ),
    ]
