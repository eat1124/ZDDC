# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.db import models
from django.contrib.auth.models import User

class App(models.Model):
    name = models.CharField(u"应用名称",  max_length=100)
    code = models.CharField(u"应用编号", blank=True, max_length=50)
    remark = models.CharField(u"说明", blank=True, null=True, max_length=5000)
    sort = models.IntegerField(u"排序", blank=True, null=True)
    state = models.CharField(u"状态", blank=True, max_length=20)


class Fun(models.Model):
    pnode = models.ForeignKey('self', blank=True, null=True, related_name='children', verbose_name='父节点')
    name = models.CharField(u"功能名称", max_length=100)
    app = models.ManyToManyField(App)
    sort = models.IntegerField(u"排序", blank=True, null=True)
    funtype = models.CharField(u"类型", blank=True, null=True, max_length=20)
    url = models.CharField(u"地址", blank=True, null=True, max_length=500)
    icon = models.CharField(u"图标", blank=True, null=True, max_length=100)
    state = models.CharField(u"状态", blank=True, null=True, max_length=20)


class Group(models.Model):
    name = models.CharField(u"组名", blank=True, null=True, max_length=50)
    fun = models.ManyToManyField(Fun)
    remark = models.CharField(u"说明", blank=True, null=True, max_length=5000)
    state = models.CharField(u"状态", blank=True, null=True, max_length=20)
    sort = models.IntegerField(u"排序", blank=True, null=True)


class UserInfo(models.Model):
    user = models.OneToOneField(User, blank=True, null=True, )
    userGUID = models.CharField(u"GUID", null=True, max_length=50)
    fullname = models.CharField(u"姓名", blank=True, max_length=50)
    phone = models.CharField(u"电话", blank=True, null=True, max_length=50)
    group = models.ManyToManyField(Group)
    pnode = models.ForeignKey('self', blank=True, null=True, related_name='children', verbose_name='父节点')
    usertype = models.CharField(u"类型", blank=True, null=True, max_length=20)
    state = models.CharField(u"状态", blank=True, null=True, max_length=20)
    sort = models.IntegerField(u"排序", blank=True, null=True)
    remark = models.CharField(u"说明", blank=True, null=True, max_length=5000)
    company = models.CharField(u"公司", blank=True, null=True, max_length=100)
    tell = models.CharField(u"电话", blank=True, null=True, max_length=50)
    forgetpassword = models.CharField(u"修改密码地址", blank=True, null=True, max_length=50)


class Dictindex(models.Model):
    name = models.CharField(u"字典名称",  max_length=100)
    remark = models.CharField(u"说明", blank=True, null=True, max_length=5000)
    sort = models.IntegerField(u"排序", blank=True, null=True)
    state = models.CharField(u"状态", blank=True, max_length=20)

class Dictlist(models.Model):
    dictindex = models.ForeignKey(Dictindex)
    name = models.CharField(u"条目名称",  max_length=100)
    remark = models.CharField(u"说明", blank=True, null=True, max_length=5000)
    sort = models.IntegerField(u"排序", blank=True, null=True)
    state = models.CharField(u"状态", blank=True, max_length=20)

class Source(models.Model):
    pnode = models.ForeignKey('self', blank=True, null=True, related_name='children', verbose_name='父节点')
    name = models.CharField(u"数据源名称", max_length=100)
    code = models.CharField(u"数据源代码", blank=True, max_length=50)
    sourcetype = models.CharField(u"类型", blank=True, null=True, max_length=20)
    connection = models.CharField(u"连接串", blank=True, null=True, max_length=500)
    sort = models.IntegerField(u"排序", blank=True, null=True)
    state = models.CharField(u"状态", blank=True, null=True, max_length=20)

class Cycle(models.Model):
    name = models.CharField(u"周期名称", max_length=100)
    code = models.CharField(u"周期代码", blank=True, max_length=50)
    minutes =models.IntegerField(u"分钟", blank=True, null=True)
    creatdate = models.DateTimeField(u"开始时间", blank=True, null=True)
    sort = models.IntegerField(u"排序", blank=True, null=True)
    state = models.CharField(u"状态", blank=True, null=True, max_length=20)

class Storage(models.Model):
    name = models.CharField(u"存储名称", max_length=100)
    code = models.CharField(u"存储代码", blank=True, max_length=50)
    tablename = models.CharField(u"表名", blank=True, max_length=200)
    storagetype = models.CharField(u"存储类型", blank=True, null=True, max_length=20)
    validtime = models.CharField(u"数据有效时间", blank=True, null=True, max_length=20)
    sort = models.IntegerField(u"排序", blank=True, null=True)
    state = models.CharField(u"状态", blank=True, null=True, max_length=20)

class Target(models.Model):
    name = models.CharField(u"指标名称", max_length=100)
    code = models.CharField(u"指标代码", blank=True, max_length=50)
    operationtype = models.CharField(u"操作类型", blank=True, max_length=20)
    cycletype = models.CharField(u"周期类型", blank=True, max_length=20)
    businesstype = models.CharField(u"业务类型", blank=True, max_length=20)
    unit = models.CharField(u"机组", blank=True, max_length=20)
    adminapp = models.ForeignKey(App,related_name='target_adminapp_set')
    app = models.ManyToManyField(App,related_name='target_app_set')
    magnification = models.DecimalField(u"倍率",max_digits=18, decimal_places=5)
    digit = models.IntegerField(u"保留位数", blank=True, null=True)
    cumulative = models.CharField(u"是否累计", max_length=20)
    upperlimit = models.DecimalField(u"上限",max_digits=20, decimal_places=5)
    lowerlimit = models.DecimalField(u"下限",max_digits=20, decimal_places=5)
    formula = models.CharField(u"公式", max_length=5000)
    cycle = models.ForeignKey(Cycle)
    source = models.ForeignKey(Source)
    sourcetable = models.CharField(u"数据源表", max_length=5000)
    sourcefields = models.CharField(u"数据源字段", max_length=5000)
    sourceconditions = models.CharField(u"数据源条件", max_length=5000)
    sourcesis = models.CharField(u"数据源sis点", max_length=5000)
    storage = models.ForeignKey(Storage)
    storagefields = models.CharField(u"存储字段", max_length=5000)
    storagetag = models.CharField(u"存储标识", max_length=200)
    sort = models.IntegerField(u"排序", blank=True, null=True)
    state = models.CharField(u"状态", blank=True, null=True, max_length=20)
    remark = models.CharField("说明", blank=True, null=True, max_length=5000)

