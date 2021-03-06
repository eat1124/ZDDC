# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.db import models
from django.contrib.auth.models import User
from django.db import connection


class App(models.Model):
    name = models.CharField("应用名称", max_length=100)
    code = models.CharField("应用编号", blank=True, max_length=50)
    remark = models.TextField("说明", blank=True, null=True)
    sort = models.IntegerField("排序", blank=True, null=True)
    state = models.CharField("状态", blank=True, max_length=20)


class Fun(models.Model):
    pnode = models.ForeignKey('self', blank=True, null=True, related_name='children', verbose_name='父节点')
    name = models.CharField("功能名称", max_length=100)
    app = models.ForeignKey(App, blank=True, null=True)
    work = models.ForeignKey('Work', null=True, verbose_name='业务')
    sort = models.IntegerField("排序", blank=True, null=True)
    funtype = models.CharField("类型", blank=True, null=True, max_length=20)
    url = models.CharField("地址", blank=True, null=True, max_length=256)
    icon = models.CharField("图标", blank=True, null=True, max_length=100)
    state = models.CharField("状态", blank=True, null=True, max_length=20)
    if_new_wd = models.CharField("是否新窗口打开", null=True, blank="0", max_length=20)


class Group(models.Model):
    name = models.CharField("组名", blank=True, null=True, max_length=50)
    fun = models.ManyToManyField(Fun)
    remark = models.TextField("说明", blank=True, null=True)
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
    remark = models.TextField("说明", blank=True, null=True)
    company = models.CharField("公司", blank=True, null=True, max_length=100)
    tell = models.CharField("电话", blank=True, null=True, max_length=50)
    forgetpassword = models.CharField("修改密码地址", blank=True, null=True, max_length=50)
    login_count = models.IntegerField("登录次数", blank=True, null=True, default=0)
    retry_time = models.DateTimeField("重试时间", blank=True, null=True)


class DictIndex(models.Model):
    name = models.CharField("字典名称", max_length=100)
    remark = models.TextField("说明", blank=True, null=True)
    sort = models.IntegerField("排序", blank=True, null=True)
    state = models.CharField("状态", blank=True, max_length=20)


class DictList(models.Model):
    dictindex = models.ForeignKey(DictIndex)
    name = models.CharField("条目名称", max_length=100)
    remark = models.TextField("说明", blank=True, null=True)
    sort = models.IntegerField("排序", blank=True, null=True)
    state = models.CharField("状态", blank=True, max_length=20)


class Source(models.Model):
    pnode = models.ForeignKey('self', blank=True, null=True, related_name='children', verbose_name='父节点')
    name = models.CharField("数据源名称", max_length=100)
    code = models.CharField("数据源代码", blank=True, max_length=50)
    sourcetype = models.CharField("类型", blank=True, null=True, max_length=20)
    connection = models.TextField("连接串", blank=True, null=True)
    sort = models.IntegerField("排序", blank=True, null=True)
    state = models.CharField("状态", blank=True, null=True, max_length=20)
    create_time = models.DateTimeField("启动时间", blank=True, null=True)
    last_time = models.DateTimeField("最近取数时间", blank=True, null=True)
    status = models.CharField("状态", blank=True, max_length=50, default="")
    p_id = models.CharField("进程ID", blank=True, max_length=50, default="")
    type = models.CharField("类型：动态类型为空字符串，固定类型(数据补取：1，数据清理：2，数据服务：3，短信服务：4)", blank=True, default='', max_length=20)


class Cycle(models.Model):
    name = models.CharField("周期名称", max_length=100)
    sort = models.IntegerField("排序", blank=True, null=True)
    state = models.CharField("状态", blank=True, null=True, max_length=20)
    schedule_type_choices = (
        (1, "每日"),
        (2, "每周"),
        (3, "每月"),
        (4, "每小时"),
    )
    schedule_type = models.IntegerField(choices=schedule_type_choices, default=1, null=True)


class SubCycle(models.Model):
    cycle = models.ForeignKey(Cycle, null=True, verbose_name='周期')
    minute = models.CharField('分钟', max_length=64, default='', blank=True)
    hour = models.CharField('小时', max_length=64, default='', blank=True)
    day_of_week = models.CharField('周中日', max_length=64, default='', blank=True)
    day_of_month = models.CharField('月中日', max_length=64, default='', blank=True)
    min_of_hour = models.CharField('时中分', max_length=64, default='', blank=True)
    state = models.CharField("状态", blank=True, null=True, max_length=20)


class Storage(models.Model):
    name = models.CharField("存储名称", max_length=100)
    tablename = models.CharField("表名", blank=True, max_length=200)
    storagetype = models.CharField("存储类型", blank=True, null=True, max_length=20)
    validtime = models.CharField("数据有效时间", blank=True, null=True, max_length=20)
    sort = models.IntegerField("排序 ", blank=True, null=True)
    state = models.CharField("状态", blank=True, null=True, max_length=20)


class Target(models.Model):
    name = models.CharField("指标名称", max_length=100)
    code = models.CharField("指标代码", db_index=True, blank=True, max_length=50)
    operationtype = models.CharField("操作类型", blank=True, max_length=20)
    cycletype = models.CharField("周期类型", blank=True, max_length=20)
    businesstype = models.CharField("业务类型", blank=True, max_length=20)
    unit = models.CharField("机组", blank=True, max_length=20)
    datatype = models.CharField("数据类型", blank=True, null=True, max_length=20)
    adminapp = models.ForeignKey(App, null=True, related_name='target_adminapp_set')
    app = models.ManyToManyField(App, related_name='target_app_set')
    magnification = models.DecimalField("倍率", null=True, max_digits=18, decimal_places=5)
    digit = models.IntegerField("保留位数", blank=True, null=True)
    cumulative = models.CharField("累计类型", null=True, max_length=20, choices=(
        ('0', '不累计'),
        ('1', '求和'),
        ('2', '算术平均'),
        ('3', '加权平均'),
        ('4', '非零算术平均'),
        ('5', '求和(上月)(环保专用)')
    ))
    weight_target = models.ForeignKey("self", null=True, verbose_name='加权指标')
    upperlimit = models.DecimalField("上限", null=True, max_digits=20, decimal_places=5)
    lowerlimit = models.DecimalField("下限", null=True, max_digits=20, decimal_places=5)
    formula = models.TextField("公式", blank=True, null=True)
    calculateguid = models.CharField("计算GUID", null=True, max_length=50)
    cycle = models.ForeignKey(Cycle, null=True)
    source = models.ForeignKey(Source, null=True)

    source_content = models.TextField('数据源内容', blank=True, null=True)

    storage = models.ForeignKey(Storage, null=True)
    storagefields = models.TextField("存储字段", blank=True, null=True)
    storagetag = models.CharField("存储标识", blank=True, null=True, max_length=200)
    sort = models.IntegerField("排序", blank=True, null=True)
    state = models.CharField("状态", blank=True, null=True, max_length=20)
    remark = models.TextField("说明", blank=True, null=True)

    work = models.ForeignKey('Work', null=True, verbose_name='业务')
    unity = models.CharField("单位", blank=True, null=True, max_length=20)
    is_repeat = models.CharField("数据重复时", blank=True, null=True, max_length=20)
    data_from_choices = (
        ("lc", '本地系统'),
        ("et", '外部系统'),
    )
    data_from = models.CharField("数据来源", null=True, max_length=20, choices=data_from_choices, default="lc")

    # 数据推送
    if_push = models.CharField("是否推送", null=True, max_length=20, default="0")
    push_config = models.TextField("推送配置:{'dest_fields': ['', ''], 'origin_source': '', 'constraint_fields': [''], 'dest_table': '', 'origin_fields': ['', '']}", null=True)
    is_select = models.CharField("是否查询", null=True, max_length=20)
    warn_range = models.IntegerField("报警范围", blank=True, null=True)


class Constant(models.Model):
    """
    常数维护
    """
    name = models.CharField("常数名称", max_length=100)
    code = models.CharField("常数代码", blank=True, max_length=50)
    adminapp = models.ForeignKey(App, null=True, related_name='constant_adminapp_set')
    sort = models.IntegerField("排序", blank=True, null=True)
    state = models.CharField("状态", blank=True, null=True, max_length=20)
    unity = models.CharField("单位", blank=True, null=True, max_length=20)
    value = models.DecimalField("常数值", null=True, max_digits=20, decimal_places=5)


class ReportModel(models.Model):
    """
    报表模板
    """
    app = models.ForeignKey(App, null=True)
    name = models.CharField("报表名称", max_length=100)
    code = models.CharField("报表编码", blank=True, max_length=50)
    file_name = models.CharField("文件名称", blank=True, null=True, max_length=50)
    report_type = models.CharField("报表类型", blank=True, null=True, max_length=20)
    if_template = models.IntegerField("是否公共报表模板", null=True, default=0, choices=(
        (1, "是"),
        (0, "否")
    ))
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
    source = models.ForeignKey(Source, null=True, verbose_name='数据源')
    app_admin = models.ForeignKey(App, null=True, verbose_name='管理应用')
    cycle = models.ForeignKey(Cycle, null=True, verbose_name='周期')
    p_id = models.CharField("进程ID", blank=True, max_length=50, default="")
    last_time = models.DateTimeField("最近取数时间", blank=True, null=True)
    name = models.CharField("进程名称", max_length=100, blank=True, null=True)
    process_path = models.CharField("进程路径", max_length=100, blank=True, null=True)
    create_time = models.DateTimeField("进程启动时间", blank=True, null=True)
    status = models.CharField("进程状态", blank=True, null=True, max_length=20)
    state = models.CharField("状态", blank=True, null=True, max_length=20)


def get_meterdata_model(prefix):
    table_name = 't_meterdata_%s' % str(prefix)

    class MeterdataMetaclass(models.base.ModelBase):
        def __new__(cls, name, bases, attrs):
            name += '_' + prefix  # 这是Model的name.
            return models.base.ModelBase.__new__(cls, name, bases, attrs)

    class Meterdata(models.Model):
        __metaclass__ = MeterdataMetaclass
        target = models.ForeignKey(Target,db_index = True)
        datadate = models.DateTimeField("开始时间", blank=True, null=True)
        zerodata = models.CharField("零点走字", null=True, max_length=20)
        twentyfourdata = models.CharField("二十四点走字", null=True, max_length=20)
        metervalue = models.CharField("电表数值", null=True, max_length=20)
        todayvalue = models.DecimalField("当前值", null=True, max_digits=22, decimal_places=7)
        judgevalue = models.DecimalField("调整值", null=True, max_digits=22, decimal_places=7, default=0)
        curvalue = models.DecimalField("最终值", null=True, max_digits=22, decimal_places=7)
        curvaluedate = models.DateTimeField("当前值", null=True)
        curvaluetext = models.CharField("当前值", null=True, max_length=20)
        cumulativemonth = models.DecimalField("月累计值", null=True, max_digits=22, decimal_places=7)
        cumulativequarter = models.DecimalField("季累计值", null=True, max_digits=22, decimal_places=7)
        cumulativehalfyear = models.DecimalField("半年累计值", null=True, max_digits=22, decimal_places=7)
        cumulativeyear = models.DecimalField("年累计值", null=True, max_digits=22, decimal_places=7)
        state = models.CharField("状态", blank=True, null=True, max_length=20)
        releasestate = models.CharField('发布状态', blank=True, default=0, max_length=10)

        @staticmethod
        def is_exists():
            return table_name in connection.introspection.table_names()

        class Meta:
            db_table = table_name

    return Meterdata


def get_entrydata_model(prefix):
    table_name = 't_entrydata_%s' % str(prefix)

    class EntrydataMetaclass(models.base.ModelBase):
        def __new__(cls, name, bases, attrs):
            name += '_' + prefix  # 这是Model的name.
            return models.base.ModelBase.__new__(cls, name, bases, attrs)

    class Entrydata(models.Model):
        __metaclass__ = EntrydataMetaclass
        target = models.ForeignKey(Target,db_index = True)
        datadate = models.DateTimeField("开始时间", blank=True, null=True)
        todayvalue = models.DecimalField("当前值", null=True, max_digits=22, decimal_places=7)
        judgevalue = models.DecimalField("调整值", null=True, max_digits=22, decimal_places=7, default=0)
        curvalue = models.DecimalField("最终值", null=True, max_digits=22, decimal_places=7)
        curvaluedate = models.DateTimeField("当前值", null=True)
        curvaluetext = models.CharField("当前值", null=True, max_length=20)
        cumulativemonth = models.DecimalField("月累计值", null=True, max_digits=22, decimal_places=7)
        cumulativequarter = models.DecimalField("季累计值", null=True, max_digits=22, decimal_places=7)
        cumulativehalfyear = models.DecimalField("半年累计值", null=True, max_digits=22, decimal_places=7)
        cumulativeyear = models.DecimalField("年累计值", null=True, max_digits=22, decimal_places=7)
        state = models.CharField("状态", blank=True, null=True, max_length=20)
        releasestate = models.CharField('发布状态', blank=True, default=0, max_length=10)

        @staticmethod
        def is_exists():
            return table_name in connection.introspection.table_names()

        class Meta:
            db_table = table_name

    return Entrydata


def get_extractdata_model(prefix):
    table_name = 't_extractdata_%s' % str(prefix)

    class ExtractdataMetaclass(models.base.ModelBase):
        def __new__(cls, name, bases, attrs):
            name += '_' + prefix  # 这是Model的name.
            return models.base.ModelBase.__new__(cls, name, bases, attrs)

    class Extractdata(models.Model):
        __metaclass__ = ExtractdataMetaclass
        target = models.ForeignKey(Target,db_index = True)
        datadate = models.DateTimeField("开始时间", blank=True, null=True)
        todayvalue = models.DecimalField("当前值", null=True, max_digits=22, decimal_places=7)
        judgevalue = models.DecimalField("调整值", null=True, max_digits=22, decimal_places=7, default=0)
        curvalue = models.DecimalField("最终值", null=True, max_digits=22, decimal_places=7)
        curvaluedate = models.DateTimeField("当前值", null=True)
        curvaluetext = models.CharField("当前值", null=True, max_length=20)
        cumulativemonth = models.DecimalField("月累计值", null=True, max_digits=22, decimal_places=7)
        cumulativequarter = models.DecimalField("季累计值", null=True, max_digits=22, decimal_places=7)
        cumulativehalfyear = models.DecimalField("半年累计值", null=True, max_digits=22, decimal_places=7)
        cumulativeyear = models.DecimalField("年累计值", null=True, max_digits=22, decimal_places=7)
        state = models.CharField("状态", blank=True, null=True, max_length=20)
        releasestate = models.CharField('发布状态', blank=True, default=0, max_length=10)

        @staticmethod
        def is_exists():
            return table_name in connection.introspection.table_names()

        class Meta:
            db_table = table_name

    return Extractdata


def get_calculatedata_model(prefix):
    table_name = 't_calculatedata_%s' % str(prefix)

    class CalculatedataMetaclass(models.base.ModelBase):
        def __new__(cls, name, bases, attrs):
            name += '_' + prefix  # 这是Model的name.
            return models.base.ModelBase.__new__(cls, name, bases, attrs)

    class Calculatedata(models.Model):
        __metaclass__ = CalculatedataMetaclass
        target = models.ForeignKey(Target,db_index = True)
        datadate = models.DateTimeField("开始时间", blank=True, null=True)
        todayvalue = models.DecimalField("当前值", null=True, max_digits=22, decimal_places=7)
        judgevalue = models.DecimalField("调整值", null=True, max_digits=22, decimal_places=7, default=0)
        curvalue = models.DecimalField("最终值", null=True, max_digits=22, decimal_places=7)
        curvaluedate = models.DateTimeField("当前值", null=True)
        curvaluetext = models.CharField("当前值", null=True, max_length=20)
        cumulativemonth = models.DecimalField("月累计值", null=True, max_digits=22, decimal_places=7)
        cumulativequarter = models.DecimalField("季累计值", null=True, max_digits=22, decimal_places=7)
        cumulativehalfyear = models.DecimalField("半年累计值", null=True, max_digits=22, decimal_places=7)
        cumulativeyear = models.DecimalField("年累计值", null=True, max_digits=22, decimal_places=7)
        formula = models.TextField("公式", blank=True, null=True)
        state = models.CharField("状态", blank=True, null=True, max_length=20)
        releasestate = models.CharField('发布状态', blank=True, default=0, max_length=10)

        @staticmethod
        def is_exists():
            return table_name in connection.introspection.table_names()

        class Meta:
            db_table = table_name

    return Calculatedata


class Meterchangedata(models.Model):
    """
    电表走字换表
    """
    meterdata = models.IntegerField('电表数据id', blank=True, null=True)
    datadate = models.DateTimeField("开始时间", blank=True, null=True)
    oldtable_zerodata = models.DecimalField("旧表起始走字", null=True, max_digits=22, decimal_places=7)
    oldtable_twentyfourdata = models.DecimalField("旧表最终走字", null=True, max_digits=22, decimal_places=7)
    oldtable_value = models.DecimalField("旧表差值", null=True, max_digits=22, decimal_places=7)
    oldtable_magnification = models.DecimalField("旧表倍率", null=True, max_digits=18, decimal_places=5)
    oldtable_finalvalue = models.DecimalField("旧表最终值", null=True, max_digits=22, decimal_places=7)
    newtable_zerodata = models.DecimalField("新表起始走字", null=True, max_digits=22, decimal_places=7)
    newtable_twentyfourdata = models.DecimalField("新表最终走字", null=True, max_digits=22, decimal_places=7)
    newtable_value = models.DecimalField("新表差值", null=True, max_digits=22, decimal_places=7)
    newtable_magnification = models.DecimalField("新表倍率", null=True, max_digits=18, decimal_places=5)
    newtable_finalvalue = models.DecimalField("新表最终值", null=True, max_digits=22, decimal_places=7)
    finalvalue = models.DecimalField("最终计算值", null=True, max_digits=22, decimal_places=7)
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
    value = models.CharField("默认值", max_length=2000)
    state = models.CharField("状态", blank=True, null=True, max_length=20)


class ExceptionData(models.Model):
    """
    异常数据
    """
    target = models.ForeignKey(Target, null=True, verbose_name='指标')
    source = models.ForeignKey(Source, null=True, verbose_name='数据源')
    app = models.ForeignKey(App, null=True, verbose_name='应用')
    cycle = models.ForeignKey(Cycle, null=True, verbose_name='周期')
    extract_error_time = models.DateTimeField('取数失败时间', null=True, blank=True)
    supplement_times = models.IntegerField('补取次数', null=True, default=0)
    last_supplement_time = models.DateTimeField('最新补取时间', null=True, blank=True)
    state = models.CharField("状态", blank=True, null=True, max_length=20)


class LogInfo(models.Model):
    """
    日志信息
    """
    source = models.ForeignKey(Source, null=True, verbose_name='数据源')
    app = models.ForeignKey(App, null=True, verbose_name='应用')
    cycle = models.ForeignKey(Cycle, null=True, verbose_name='周期')
    create_time = models.DateTimeField('时间', null=True, blank=True)
    content = models.TextField('日志内容', null=True, blank=True)


class Work(models.Model):
    """
    业务字表: 业务名称、业务编号、说明、排序、核心业务（是/否选项，只能有一个核心业务）
    """
    app = models.ForeignKey(App, null=True, verbose_name='应用')
    name = models.CharField('业务名称', blank=True, default='', max_length=64)
    code = models.CharField('业务编号', blank=True, default='', max_length=128)
    remark = models.TextField('说明', blank=True, default='')
    sort = models.IntegerField('排序', default=0)
    core = models.CharField('是否核心业务', blank=True, default='否', max_length=20)
    state = models.CharField('状态', blank=True, default='', max_length=20)


class ReportServer(models.Model):
    """
    报表服务器
    """
    ps_script_path = models.CharField("POWERSHELL脚本存放位置", blank=True, default='', max_length=256)
    report_file_path = models.CharField("报表服务器存放文件路径", blank=True, default='', max_length=256)
    web_server = models.CharField("Web服务器地址:127.0.0.1:8000", blank=True, default='', max_length=256)
    report_server = models.CharField("报表服务器地址", blank=True, default='', max_length=256)
    username = models.CharField("报表服务器用户名", blank=True, default='', max_length=256)
    password = models.CharField("报表服务器密码", blank=True, default='', max_length=256)


class ReportingLog(models.Model):
    """
    填报日志表
    """
    adminapp = models.ForeignKey(App, null=True, related_name='reportlog_adminapp_set')
    work = models.ForeignKey('Work', null=True, verbose_name='业务')
    cycletype = models.CharField("周期类型", blank=True, max_length=20)
    operationtype = models.CharField("操作类型", blank=True, max_length=20)
    datadate = models.DateTimeField("报表时间", blank=True, null=True)
    write_time = models.DateTimeField("制表时间", blank=True, null=True)
    user = models.OneToOneField(User, blank=True, null=True)
    type = models.CharField("类型", blank=True, null=True, max_length=20)
    state = models.CharField("状态", blank=True, null=True, max_length=20)


class UpdateDataLog(models.Model):
    """
    变更数据记录表
    """
    target = models.ForeignKey(Target, db_index=True)
    adminapp = models.ForeignKey(App, null=True, related_name='updatedatalog_adminapp_set')
    work = models.ForeignKey('Work', null=True, verbose_name='业务')
    user = models.ForeignKey(User, blank=True, null=True, verbose_name="变更人")
    cycletype = models.CharField("周期类型", blank=True, max_length=20)
    operationtype = models.CharField("操作类型", blank=True, max_length=20)
    datadate = models.DateTimeField("数据时间", blank=True, null=True)
    write_time = models.DateTimeField("变更时间时间", blank=True, null=True)
    before_curvalue = models.DecimalField("变更前数据", null=True, max_digits=22, decimal_places=7)
    after_curvalue = models.DecimalField("变更后数据", null=True, max_digits=22, decimal_places=7)
    raw_curvalue = models.DecimalField("原始数据", null=True, max_digits=22, decimal_places=7)
    state = models.CharField("状态", blank=True, null=True, max_length=20)


class SupplementProcess(models.Model):
    """
    补取进程表
    """
    primary_process = models.ForeignKey(ProcessMonitor, null=True, verbose_name='主进程表')
    p_id = models.CharField("进程ID", blank=True, max_length=50, default="")
    setup_time = models.DateTimeField('启动时间：点击补取的当前时间', null=True)
    update_time = models.DateTimeField('更新时间：一分钟写一次，系统时间', null=True)
    p_state = models.CharField('进程状态：1/0', max_length=10, null=True, blank=True)
    start_time = models.DateTimeField('补取开始时间', null=True)
    end_time = models.DateTimeField('补取结束时间', null=True)
    progress_time = models.DateTimeField('补取进度时间：一分钟写一次，取数时间', null=True)
    state = models.CharField('状态', max_length=10, null=True, blank=True)


class TargetStatistic(models.Model):
    """
    指标统计查询
    """
    name = models.CharField("查询名", max_length=256, null=True, default="")
    type = models.CharField("查询周期类型", max_length=20, null=True, default="")
    remark = models.TextField("查询说明", null=True, default="")
    col_data = models.TextField("指标列JSON信息", null=True, default="")
    state = models.CharField('状态', max_length=10, null=True, default="")
    sort = models.IntegerField("排序", blank=True, null=True)
    user = models.ForeignKey(UserInfo, null=True, verbose_name="权限用户")


class ElectricEnergy(models.Model):
    """
    上网电量
    """
    f_electric_energy = models.DecimalField("#1上网电量", null=True, max_digits=22, decimal_places=7)
    s_electric_energy = models.DecimalField("#2上网电量", null=True, max_digits=22, decimal_places=7)
    a_electric_energy = models.DecimalField("总上网电量", null=True, max_digits=22, decimal_places=7)
    extract_time = models.DateTimeField("取数时间", null=True)
    state = models.CharField('状态', max_length=10, null=True, blank=True)
