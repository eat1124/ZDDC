# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.db import models
from django.contrib.auth.models import User


class App(models.Model):
    name = models.CharField("应用名称", max_length=100)
    code = models.CharField("应用编号", blank=True, max_length=50)
    remark = models.CharField("说明", blank=True, null=True, max_length=2000)
    sort = models.IntegerField("排序", blank=True, null=True)
    state = models.CharField("状态", blank=True, max_length=20)


class Fun(models.Model):
    pnode = models.ForeignKey('self', blank=True, null=True, related_name='children', verbose_name='父节点')
    name = models.CharField("功能名称", max_length=100)
    app = models.ForeignKey(App, blank=True, null=True)
    sort = models.IntegerField("排序", blank=True, null=True)
    funtype = models.CharField("类型", blank=True, null=True, max_length=20)
    url = models.CharField("地址", blank=True, null=True, max_length=500)
    icon = models.CharField("图标", blank=True, null=True, max_length=100)
    state = models.CharField("状态", blank=True, null=True, max_length=20)


class Group(models.Model):
    name = models.CharField("组名", blank=True, null=True, max_length=50)
    fun = models.ManyToManyField(Fun)
    remark = models.CharField("说明", blank=True, null=True, max_length=2000)
    state = models.CharField("状态", blank=True, null=True, max_length=20)
    sort = models.IntegerField("排序", blank=True, null=True)


class UserInfo(models.Model):
    user = models.OneToOneField(User, blank=True, null=True)
    userGUID = models.CharField("GUID", null=True, max_length=50)
    fullname = models.CharField("姓名", blank=True, max_length=50)
    phone = models.CharField("电话", blank=True, null=True, max_length=50)
    group = models.ManyToManyField(Group)
    pnode = models.ForeignKey('self', blank=True, null=True, related_name='children', verbose_name='父节点')
    usertype = models.CharField("类型", blank=True, null=True, max_length=20)
    state = models.CharField("状态", blank=True, null=True, max_length=20)
    sort = models.IntegerField("排序", blank=True, null=True)
    remark = models.CharField("说明", blank=True, null=True, max_length=2000)
    company = models.CharField("公司", blank=True, null=True, max_length=100)
    tell = models.CharField("电话", blank=True, null=True, max_length=50)
    forgetpassword = models.CharField("修改密码地址", blank=True, null=True, max_length=50)


class DictIndex(models.Model):
    name = models.CharField("字典名称", max_length=100)
    remark = models.CharField("说明", blank=True, null=True, max_length=2000)
    sort = models.IntegerField("排序", blank=True, null=True)
    state = models.CharField("状态", blank=True, max_length=20)


class DictList(models.Model):
    dictindex = models.ForeignKey(DictIndex)
    name = models.CharField("条目名称", max_length=100)
    remark = models.CharField("说明", blank=True, null=True, max_length=2000)
    sort = models.IntegerField("排序", blank=True, null=True)
    state = models.CharField("状态", blank=True, max_length=20)


class Source(models.Model):
    pnode = models.ForeignKey('self', blank=True, null=True, related_name='children', verbose_name='父节点')
    name = models.CharField("数据源名称", max_length=100)
    code = models.CharField("数据源代码", blank=True, max_length=50)
    sourcetype = models.CharField("类型", blank=True, null=True, max_length=20)
    connection = models.CharField("连接串", blank=True, null=True, max_length=500)
    sort = models.IntegerField("排序", blank=True, null=True)
    state = models.CharField("状态", blank=True, null=True, max_length=20)
    create_time = models.DateTimeField("启动时间", blank=True, null=True)
    last_time = models.DateTimeField("最近取数时间", blank=True, null=True)
    status = models.CharField("状态", blank=True, max_length=50, default="")
    p_id = models.CharField("进程ID", blank=True, max_length=50, default="")

class Cycle(models.Model):
    name = models.CharField("周期名称", max_length=100)
    code = models.CharField("周期代码", blank=True, max_length=50)
    minutes = models.IntegerField("分钟", blank=True, null=True)
    creatdate = models.DateTimeField("开始时间", blank=True, null=True)
    sort = models.IntegerField("排序", blank=True, null=True)
    state = models.CharField("状态", blank=True, null=True, max_length=20)


class Storage(models.Model):
    name = models.CharField("存储名称", max_length=100)
    code = models.CharField("存储代码", blank=True, max_length=50)
    tablename = models.CharField("表名", blank=True, max_length=200)
    storagetype = models.CharField("存储类型", blank=True, null=True, max_length=20)
    validtime = models.CharField("数据有效时间", blank=True, null=True, max_length=20)
    sort = models.IntegerField("排序 ", blank=True, null=True)
    state = models.CharField("状态", blank=True, null=True, max_length=20)


class Target(models.Model):
    name = models.CharField("指标名称", max_length=100)
    code = models.CharField("指标代码", blank=True, max_length=50)
    operationtype = models.CharField("操作类型", blank=True, max_length=20)
    cycletype = models.CharField("周期类型", blank=True, max_length=20)
    businesstype = models.CharField("业务类型", blank=True, max_length=20)
    unit = models.CharField("机组", blank=True, max_length=20)
    datatype = models.CharField("数据类型", blank=True, null=True, max_length=20)
    adminapp = models.ForeignKey(App, null=True, related_name='target_adminapp_set')
    app = models.ManyToManyField(App, related_name='target_app_set')
    magnification = models.DecimalField("倍率", null=True, max_digits=18, decimal_places=5)
    digit = models.IntegerField("保留位数", blank=True, null=True)
    cumulative = models.CharField("是否累计", blank=True, null=True, max_length=20)
    upperlimit = models.DecimalField("上限", null=True, max_digits=20, decimal_places=5)
    lowerlimit = models.DecimalField("下限", null=True, max_digits=20, decimal_places=5)
    formula = models.CharField("公式", blank=True, null=True, max_length=2000)
    calculateguid = models.CharField(u"计算GUID", null=True, max_length=50)
    cycle = models.ForeignKey(Cycle, null=True)
    source = models.ForeignKey(Source, null=True)
    sourcetable = models.CharField("数据源表", blank=True, null=True, max_length=2000)
    sourcefields = models.CharField("数据源字段", blank=True, null=True, max_length=2000)
    sourceconditions = models.CharField("数据源条件", blank=True, null=True, max_length=2000)
    sourcesis = models.CharField("数据源sis点", blank=True, null=True, max_length=2000)
    storage = models.ForeignKey(Storage, null=True)
    storagefields = models.CharField("存储字段", blank=True, null=True, max_length=2000)
    storagetag = models.CharField("存储标识", blank=True, null=True, max_length=200)
    sort = models.IntegerField("排序", blank=True, null=True)
    state = models.CharField("状态", blank=True, null=True, max_length=20)
    remark = models.CharField("说明", blank=True, null=True, max_length=2000)


class ReportModel(models.Model):
    """
    报表模板
    """
    app = models.ForeignKey(App)
    name = models.CharField("报表名称", max_length=100)
    code = models.CharField("报表编码", blank=True, max_length=50)
    file_name = models.CharField("文件名称", blank=True, null=True, max_length=50)
    report_type = models.CharField("报表类型", blank=True, null=True, max_length=20)
    sort = models.IntegerField("排序", blank=True, null=True)
    state = models.CharField("状态", blank=True, null=True, max_length=20)


class ReportInfo(models.Model):
    """
    报表所需信息
    """
    report_model = models.ForeignKey(ReportModel)
    name = models.CharField("信息名称", max_length=100)
    default_value = models.CharField("默认值", max_length=100)
    sort = models.IntegerField("排序", blank=True, null=True)
    state = models.CharField("状态", blank=True, null=True, max_length=20)


class ProcessMonitor(models.Model):
    """
    进程监控类
    """
    name = models.CharField("进程名称", max_length=100, blank=True, null=True)
    process_path = models.CharField("进程路径", max_length=100, blank=True, null=True)
    create_time = models.DateTimeField("进程启动时间", blank=True, null=True)
    status = models.CharField("进程状态", blank=True, null=True, max_length=20)
    state = models.CharField("状态", blank=True, null=True, max_length=20)


class Entrydata(models.Model):
    """
    录入数据
    """
    target = models.ForeignKey(Target)
    datadate = models.DateTimeField("开始时间", blank=True, null=True)
    curvalue = models.DecimalField("当前值", null=True, max_digits=20, decimal_places=5)
    cumulativemonth = models.DecimalField("月累计值", null=True, max_digits=20, decimal_places=5)
    cumulativequarter = models.DecimalField("季累计值", null=True, max_digits=20, decimal_places=5)
    cumulativehalfyear = models.DecimalField("半年累计值", null=True, max_digits=20, decimal_places=5)
    cumulativeyear = models.DecimalField("年累计值", null=True, max_digits=20, decimal_places=5)
    state = models.CharField("状态", blank=True, null=True, max_length=20)


class Extractdata(models.Model):
    """
    提取数据
    """
    target = models.ForeignKey(Target)
    datadate = models.DateTimeField("开始时间", blank=True, null=True)
    curvalue = models.DecimalField("当前值", null=True, max_digits=20, decimal_places=5)
    cumulativemonth = models.DecimalField("月累计值", null=True, max_digits=20, decimal_places=5)
    cumulativequarter = models.DecimalField("季累计值", null=True, max_digits=20, decimal_places=5)
    cumulativehalfyear = models.DecimalField("半年累计值", null=True, max_digits=20, decimal_places=5)
    cumulativeyear = models.DecimalField("年累计值", null=True, max_digits=20, decimal_places=5)
    state = models.CharField("状态", blank=True, null=True, max_length=20)


class Calculatedata(models.Model):
    """
    计算数据
    """
    target = models.ForeignKey(Target)
    datadate = models.DateTimeField("开始时间", blank=True, null=True)
    curvalue = models.DecimalField("当前值", null=True, max_digits=20, decimal_places=5)
    cumulativemonth = models.DecimalField("月累计值", null=True, max_digits=20, decimal_places=5)
    cumulativequarter = models.DecimalField("季累计值", null=True, max_digits=20, decimal_places=5)
    cumulativehalfyear = models.DecimalField("半年累计值", null=True, max_digits=20, decimal_places=5)
    cumulativeyear = models.DecimalField("年累计值", null=True, max_digits=20, decimal_places=5)
    formula = models.CharField("公式", blank=True, null=True, max_length=2000)
    state = models.CharField("状态", blank=True, null=True, max_length=20)


class ReportSubmit(models.Model):
    """
    报表上报
    """
    app = models.ForeignKey(App)
    report_model = models.ForeignKey(ReportModel)
    state = models.CharField("状态", blank=True, null=True, max_length=20)
    person = models.CharField("填报人", blank=True, null=True, max_length=100)
    write_time = models.DateTimeField("更新日期", blank=True, null=True)
    report_time = models.DateTimeField("报表时间", blank=True, null=True)


class ReportSubmitInfo(models.Model):
    """
    报表所需信息
    """
    report_submit = models.ForeignKey(ReportSubmit)
    name = models.CharField("信息名称", max_length=100)
    value = models.CharField("默认值", max_length=100)
    state = models.CharField("状态", blank=True, null=True, max_length=20)
