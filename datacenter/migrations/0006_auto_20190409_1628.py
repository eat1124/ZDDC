# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2019-04-09 16:28
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('datacenter', '0005_auto_20190408_1337'),
    ]

    operations = [
        migrations.CreateModel(
            name='calculatedata',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('curvalue', models.DecimalField(decimal_places=5, max_digits=20, null=True, verbose_name='当前值')),
                ('cumulativemonth', models.DecimalField(decimal_places=5, max_digits=20, null=True, verbose_name='月累计值')),
                ('cumulativequarter', models.DecimalField(decimal_places=5, max_digits=20, null=True, verbose_name='季累计值')),
                ('cumulativehalfyear', models.DecimalField(decimal_places=5, max_digits=20, null=True, verbose_name='半年累计值')),
                ('cumulativeyear', models.DecimalField(decimal_places=5, max_digits=20, null=True, verbose_name='年累计值')),
                ('formula', models.CharField(blank=True, max_length=2000, null=True, verbose_name='公式')),
                ('state', models.CharField(blank=True, max_length=20, null=True, verbose_name='状态')),
            ],
        ),
        migrations.CreateModel(
            name='Datamain',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cycletype', models.CharField(blank=True, max_length=20, verbose_name='周期类型')),
                ('datadate', models.DateTimeField(blank=True, null=True, verbose_name='开始时间')),
                ('state', models.CharField(blank=True, max_length=20, null=True, verbose_name='状态')),
                ('app', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='datacenter.App')),
            ],
        ),
        migrations.CreateModel(
            name='entrydata',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('curvalue', models.DecimalField(decimal_places=5, max_digits=20, null=True, verbose_name='当前值')),
                ('cumulativemonth', models.DecimalField(decimal_places=5, max_digits=20, null=True, verbose_name='月累计值')),
                ('cumulativequarter', models.DecimalField(decimal_places=5, max_digits=20, null=True, verbose_name='季累计值')),
                ('cumulativehalfyear', models.DecimalField(decimal_places=5, max_digits=20, null=True, verbose_name='半年累计值')),
                ('cumulativeyear', models.DecimalField(decimal_places=5, max_digits=20, null=True, verbose_name='年累计值')),
                ('state', models.CharField(blank=True, max_length=20, null=True, verbose_name='状态')),
                ('datamain', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='datacenter.Datamain')),
                ('target', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='datacenter.Target')),
            ],
        ),
        migrations.CreateModel(
            name='extractdata',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('curvalue', models.DecimalField(decimal_places=5, max_digits=20, null=True, verbose_name='当前值')),
                ('cumulativemonth', models.DecimalField(decimal_places=5, max_digits=20, null=True, verbose_name='月累计值')),
                ('cumulativequarter', models.DecimalField(decimal_places=5, max_digits=20, null=True, verbose_name='季累计值')),
                ('cumulativehalfyear', models.DecimalField(decimal_places=5, max_digits=20, null=True, verbose_name='半年累计值')),
                ('cumulativeyear', models.DecimalField(decimal_places=5, max_digits=20, null=True, verbose_name='年累计值')),
                ('state', models.CharField(blank=True, max_length=20, null=True, verbose_name='状态')),
                ('datamain', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='datacenter.Datamain')),
                ('target', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='datacenter.Target')),
            ],
        ),
        migrations.AddField(
            model_name='calculatedata',
            name='datamain',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='datacenter.Datamain'),
        ),
        migrations.AddField(
            model_name='calculatedata',
            name='target',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='datacenter.Target'),
        ),
    ]