"""
启动进程
"""
import os
import datetime
import time
import json
import copy
import re
import logging
from collections import OrderedDict
import calendar
import pymysql.cursors
import cx_Oracle
import pymssql
import psutil
import decimal

# 使用ORM
import sys
from django.core.wsgi import get_wsgi_application

# 获取django路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.extend([r'%s' % BASE_DIR, ])
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ZDDC.settings")
application = get_wsgi_application()
from datacenter.models import *
from django.conf import settings

# 引入C#脚本
import sys

sys.path.insert(0, os.path.join(os.path.join(BASE_DIR, 'utils'), 'dlls'))

# import clr
#
# clr.AddReference('PIApp')
# from PIApp import *

logger = logging.getLogger('process')

dict_list = DictList.objects.exclude(state='9').values('id', 'name')

# 本地数据库信息
pro_db_engine = 'MySQL'
if 'sql_server' in settings.DATABASES['default']['ENGINE']:
    pro_db_engine = 'SQLServer'

db_info = {
    'host': settings.DATABASES['default']['HOST'],
    'user': settings.DATABASES['default']['USER'],
    'passwd': settings.DATABASES['default']['PASSWORD'],
    'db': settings.DATABASES['default']['NAME'],
}


def get_dict_name(key):
    name = ''
    try:
        key = int(key)
    except:
        pass
    else:
        for dl in dict_list:
            if key == dl['id']:
                name = dl['name']
                break
    return name


class SeveralDBQuery(object):
    """
    SQL Server
    Oracle
    MySQL
    数据库取数
    """

    def __init__(self, db_type, credit):
        # [{"host":"192.168.1.66","user":"root","passwd":"password","db":"datacenter"}]
        self.db_type = db_type.replace(' ', '').upper()
        self.connection = None
        self.result = []
        self.error = ""

        try:
            if self.db_type == "MYSQL":
                self.connection = pymysql.connect(host=credit['host'],
                                                  user=credit['user'],
                                                  password=credit['passwd'],
                                                  db=credit['db'],
                                                  charset='utf8mb4',
                                                  cursorclass=pymysql.cursors.DictCursor)
            if self.db_type == 'ORACLE':
                self.connection = cx_Oracle.connect('{user}/{passwd}@{host}/{db}'.format(
                    user=credit['user'],
                    passwd=credit['passwd'],
                    host=credit['host'],
                    db=credit['db']
                ))
            if self.db_type == 'SQLSERVER':
                self.connection = pymssql.connect(
                    host=credit['host'],
                    user=credit['user'],
                    password=credit['passwd'],
                    database=credit['db']
                )
        except Exception as e:
            self.error = 'SeveralDBQuery >> __init__() >> 数据库连接失败:%s 。' % e
        else:
            if not self.connection:
                self.error = 'SeveralDBQuery >> __init__() >> 数据库未连接。'

    def fetch_all(self, fetch_sql):
        self.result = []
        try:
            if self.db_type == 'ORACLE':
                curs = self.connection.cursor()
                curs.execute(fetch_sql)
                self.result = curs.fetchall()
                curs.close()
            else:
                with self.connection.cursor() as cursor:
                    cursor.execute(fetch_sql)
                    if self.db_type == "MYSQL":
                        fixed_key = []
                        for cd in cursor.description:
                            fixed_key.append(cd[0])

                        for i in range(cursor.rowcount):
                            single_ret = cursor.fetchone()
                            tmp_result = []
                            for key in fixed_key:
                                tmp_result.append(single_ret[key])
                            self.result.append(tmp_result)

                    else:
                        self.result = cursor.fetchall()
        except Exception as e:
            self.error = fetch_sql + " 数据查询失败：%s" % e

    def update(self, update_sql):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(update_sql)
                self.connection.commit()
        except Exception as e:
            self.error = "数据插入失败：%s" % e
            return False
        else:
            return True

    def close(self):
        if self.connection:
            self.connection.close()


class PIQuery(object):
    """
    PI数据库取数
    """

    def __init__(self, connection):
        self.connection = connection

    def get_data_from_pi(self, source_content, time):
        """
        从PI中取数据
            type: avg, max, min, delta, real
            # 解析PI的数据源内容
            # tmp = 'DCS11.LAC20AP001XB83A.AV^保留为位数^real^<#D#>^<#D#>'
        :return:
        """
        result_list = []
        error = ""
        source_content = source_content.split('^')

        tag, digit, operate, start_time, end_time = source_content[0], source_content[1], 'real', '<#D#>', '<#D#>'
        if len(source_content) > 2:
            operate = source_content[2].upper()
        if len(source_content) > 3:
            start_time = source_content[3]
        if len(source_content) > 4:
            end_time = source_content[4]
        start_time = Extract.format_date(time, start_time,
                                         return_type='timestamp').strftime("%Y-%m-%d %H:%M:%S")
        end_time = Extract.format_date(time, end_time,
                                       return_type='timestamp').strftime("%Y-%m-%d %H:%M:%S")

        curvalue = None
        status = 1
        try:
            conn = self.connection['host']

            if operate == 'REAL':
                curvalue = json.loads(ManagePI.ReadHisValueFromPI(conn, tag, start_time))
            elif operate == 'AVG':
                curvalue = json.loads(ManagePI.ReadAvgValueFromPI(conn, tag, start_time, end_time))
            elif operate == 'MAX':
                curvalue = json.loads(ManagePI.ReadMaxValueFromPI(conn, tag, start_time, end_time))
            elif operate == 'MIN':
                curvalue = json.loads(ManagePI.ReadMinValueFromPI(conn, tag, start_time, end_time))
            elif operate == 'DELTA':
                curvalue = json.loads(ManagePI.ReadCzValueFromPI(conn, tag, start_time, end_time))
            else:
                curvalue = None

        except Exception as e:
            status = 0
            curvalue = e

        # 构造result_list
        if status:
            if type(curvalue) == dict:
                if curvalue['success']:
                    if curvalue['success'] == "0":
                        error = 'Extract >> get_row_data() >> PI数据获取失败：' + str(curvalue)
                    else:
                        # curvalue保留位数处理
                        if curvalue['value'] is not None and digit != "" and digit is not None:
                            try:
                                digit = int(digit)
                                curvalue['value'] = decimal.Decimal(str(curvalue['value'])).quantize(
                                    decimal.Decimal(PIQuery.quantize_digit(digit)), rounding=decimal.ROUND_HALF_UP)

                            except Exception as e:
                                logger.info("PI取数小数处理异常: " + str(e))
                        result_list = [[curvalue['value']]]
                else:
                    error = 'Extract >> get_row_data() >> PI数据获取失败：' + str(curvalue)
            elif type(curvalue) == list:
                error = 'Extract >> get_row_data() >> PI数据获取失败：' + str(curvalue)
            else:
                error = 'Extract >> get_row_data() >> PI数据获取失败：' + str(curvalue)
        else:
            error = 'Extract >> get_row_data() >> PI数据获取失败：' + str(curvalue)
        logger.info(str({"result": result_list, "error": error}))
        return {"result": result_list, "error": error}

    @staticmethod
    def quantize_digit(digit):
        """
        四舍五入quantize参数
        """
        if digit == 0:
            digit = '0'
        elif digit == 1:
            digit = '0.0'
        elif digit == 2:
            digit = '0.00'
        elif digit == 3:
            digit = '0.000'
        elif digit == 4:
            digit = '0.0000'
        elif digit == 5:
            digit = '0.00000'
        elif digit == 6:
            digit = '0.000000'
        else:
            digit = '0.0000000'
        return digit


class Extract(object):
    """
    先补取，后定时取数
    """

    def __init__(self, app_id, source_id, cycle_id):
        self.app_id = app_id
        self.source_id = source_id
        self.cycle_id = cycle_id
        self.pm = None
        try:
            self.pm = ProcessMonitor.objects.exclude(state='9').get(app_admin_id=self.app_id, source_id=self.source_id,
                                                                    cycle_id=self.cycle_id)
        except ProcessMonitor.DoesNotExist as e:
            take_notes(self.source_id, self.app_id, self.cycle_id, 'Extract >> __init__() >> %s' % e)
        else:
            if not self.pm:
                take_notes(self.source_id, self.app_id, self.cycle_id, 'Extract >> supplement() >> 该进程不存在，取数进程启动失败。')

    def supplement(self):
        # 补取
        start_time = self.pm.last_time

        if start_time:
            end_time = datetime.datetime.now()

            # start_time加上一分钟，低于end_time继续循环补取，超过则停止
            while True:
                start_time = start_time + datetime.timedelta(minutes=1)
                # 取数
                self.get_data(start_time)
                if start_time > end_time:
                    break
        else:
            take_notes(self.source_id, self.app_id, self.cycle_id, 'Extract >> supplement() >> 首次取数，不进行补取。')

        # 补取过程也消耗时间，再次判断进行补取:先把秒数抹掉再比较
        aft_last_time = self.pm.last_time

        try:
            aft_last_time = datetime.datetime.strptime('{:%Y-%m-%d %H:%M}'.format(aft_last_time), '%Y-%m-%d %H:%M')
            now_time = datetime.datetime.strptime('{:%Y-%m-%d %H:%M}'.format(datetime.datetime.now()), '%Y-%m-%d %H:%M')
        except Exception as e:
            take_notes(self.source_id, self.app_id, self.cycle_id, 'Extract >> supplement() >> %s' % e)
        else:
            try:
                delta_time = (now_time - aft_last_time).total_seconds()
            except Exception as e:
                take_notes(self.source_id, self.app_id, self.cycle_id, 'Extract >> supplement() >> %s' % e)
            else:
                if delta_time > 60:
                    self.supplement()

    def set_timer(self):
        # 定时器
        while True:
            time_now = datetime.datetime.now()

            self.get_data(time_now)
            time.sleep(60)

    def get_data(self, now_time):
        # 取数
        # 判断当前时间是否符合周期规则
        cycle_rule = self.pm.cycle
        if cycle_rule:
            schedule_type = cycle_rule.schedule_type
            minute, hour, day_of_week, day_of_month = None, None, None, None
            try:
                minute = int(cycle_rule.minute)
            except:
                pass
            try:
                hour = int(cycle_rule.hour)
            except:
                pass
            try:
                day_of_week = int(cycle_rule.day_of_week)
            except:
                pass
            try:
                day_of_month = int(cycle_rule.day_of_month)
            except:
                pass

            # 当前时间
            now_minute = now_time.minute
            now_hour = now_time.hour
            now_weekday = now_time.weekday()
            now_day = now_time.day

            if now_hour == hour and now_minute == minute:
                # 每日/每周/每月
                if schedule_type == 1:
                    self._get_data(now_time)
                if schedule_type == 2:
                    # 判断一周第几天
                    if now_weekday == day_of_week:
                        self._get_data(now_time)
                if schedule_type == 3:
                    # 判断一月第几天
                    if now_day == day_of_month:
                        self._get_data(now_time)
        self.pm.last_time = now_time
        self.pm.save()

    def _get_data(self, now_time, targets=None):
        ordered_targets = Target.objects.filter(
            adminapp_id=self.app_id, source_id=self.source_id, cycle_id=self.cycle_id
        ).exclude(state='9').order_by('storage_id', 'storagetag')

        if targets:
            # 选中指标
            ordered_targets = ordered_targets.filter(id__in=targets)
        # 行存的方式，对单个指标取数
        # 列存的方式，对相同存储标志的多个指标取数，完成之后需要剔除这些指标，避免重复
        copy_ordered_targets = copy.deepcopy(ordered_targets)
        for o_target in ordered_targets:
            storage = o_target.storage
            if storage:
                # 从DictList中获取
                storage_type_name = get_dict_name(storage.storagetype)

                if storage_type_name == '行':
                    # 未取到数据(save:指标，周期，数据源，应用)
                    if not self.get_row_data(o_target, now_time):
                        self.record_exception_data(o_target)
                elif storage_type_name == '列':
                    col_ordered_targets = copy_ordered_targets.filter(storage=storage,
                                                                      storagetag=o_target.storagetag)

                    if not self.get_col_data(col_ordered_targets, now_time):
                        for cot in col_ordered_targets:
                            self.record_exception_data(cot)

                    # 剔除
                    copy_ordered_targets = copy_ordered_targets.exclude(storage=storage,
                                                                        storagetag=o_target.storagetag)
                else:
                    take_notes(self.source_id, self.app_id, self.cycle_id,
                               'Extract >> _get_data() >> %s' % 'storage_storagetag为空。')

    @staticmethod
    def getDataFromSource(target, time):
        source = target.source
        source_type_name = ''
        result_list = []
        error = ""
        if source:
            source_type = source.sourcetype
            source_type_name = get_dict_name(source_type)

            source_connection = ''
            try:
                source_connection = eval(source.connection)
                if type(source_connection) == list:
                    source_connection = source_connection[0]
            except Exception as e:
                error = 'Extract >> getDataFromSource() >> 数据源配置认证信息错误：%s' % e
                return {"result": result_list, "error": error}
            else:
                source_content = target.source_content
                if source_type_name == 'PI':
                    pi_query = PIQuery(source_connection)
                    result = pi_query.get_data_from_pi(source_content, time)
                    result_list = result["result"]
                    error = result["error"]
                else:
                    # 匹配出<#D#>
                    date_com = re.compile('<#.*?#>')
                    pre_format_list = date_com.findall(source_content)
                    if pre_format_list:
                        format_date = Extract.format_date(time, pre_format_list[0])
                        # 格式化后的SQL
                        source_content = source_content.replace(pre_format_list[0], format_date)

                    db_query = SeveralDBQuery(source_type_name, source_connection)
                    db_query.fetch_all(source_content)
                    result_list = db_query.result
                    error = db_query.error
                    db_query.close()
        else:
            error = 'Extract >> getDataFromSource() >> 数据源不存在。'
        return {"result": result_list, "error": error}

    def save_row_data(self, target, time, result_list):
        # storagefields有4个特例，
        # 1.id，id字段不需要配置，storage表必有id字段并自增长
        # 2.target_id,target_id字段不需要配置,代码中强制保存index.id到storage的target_id字段
        # 3.savedate,savedate字段不需要配置,代码中强制保存time到storage的savedate字段
        # 4.datadate，配置时需放在普通字段之后，datadate格式如<#DATADATE:m:S#>，参考source_content中的时间格式，将time格式化后再转成日期格式保存
        result = True
        error = ""
        storagefields = target.storagefields
        storagefields_list = storagefields.split(',')

        if not result_list:
            result = False
        else:
            for result in result_list:
                storage = OrderedDict()

                for num, rt in enumerate(result):
                    storage[storagefields_list[num]] = rt

                storage["savedate"] = time
                storage['target_id'] = target.id
                date_com = re.compile('<#.*?#>')
                pre_datadate_format_list = date_com.findall(storagefields)
                if pre_datadate_format_list:
                    format_datadate = Extract.format_date(time, pre_datadate_format_list[0],
                                                          return_type='timestamp') if pre_datadate_format_list else None
                    storage['datadate'] = format_datadate

                fields = ''
                values = ''

                for k, v in storage.items():
                    # 值不为空时，写入键值对
                    fields += k.strip() + ','

                    if type(v) == str:
                        values += '"%s"' % v.strip() + ','
                    elif type(v) == datetime.datetime:
                        values += '"%s"' % str(v) + ','
                    else:
                        values += str(v) + ','

                fields = fields[:-1] if fields.endswith(',') else fields
                values = values[:-1] if values.endswith(',') else values

                tablename = target.storage.tablename
                # 行存
                row_save_sql = r"""INSERT INTO {tablename}({fields}) VALUES({values})""".format(
                    tablename=tablename, fields=fields, values=values).replace('"', "'")

                # SQL Server update操作的sql不同
                if 'sql_server' in settings.DATABASES['default']['ENGINE']:
                    row_save_sql = r"""INSERT INTO {db}.dbo.{tablename}({fields}) VALUES({values})""".format(
                        tablename=tablename, fields=fields, values=values,
                        db=settings.DATABASES['default']['NAME']).replace('"', "'")

                logger.info('行存：%s' % row_save_sql)
                db_update = SeveralDBQuery(pro_db_engine, db_info)
                ret = db_update.update(row_save_sql)
                db_update.close()
                result = ret
                if not result:
                    error = db_update.error
                else:
                    # 行存推送
                    result, error = self.push_data(target, storage, result=result, error=error)
        return {"result": result, "error": error}

    def get_row_data(self, target, time):

        source = target.source
        # 从数据库取数
        result = Extract.getDataFromSource(target, time)
        result_list = result["result"]
        result_error = result["error"]
        if result_error:
            take_notes(self.source_id, self.app_id, self.cycle_id, result_error)

        if result_list:
            # 保存数据
            save_result = self.save_row_data(target, time, result_list)
            saveresult = save_result["result"]
            saveerror = save_result["error"]
            if saveerror:
                take_notes(self.source_id, self.app_id, self.cycle_id, saveerror)
            if saveresult:
                return True
            else:
                return False
        else:
            return False

    def save_col_data(self, target, time, storage):
        result = True
        error = ""

        storage["savedate"] = time
        date_com = re.compile('<#.*?#>')
        storagefields = target.storagefields
        pre_datadate_format_list = date_com.findall(storagefields)
        if pre_datadate_format_list:
            format_datadate = Extract.format_date(time, pre_datadate_format_list[0],
                                                  return_type='timestamp') if pre_datadate_format_list else None
            storage['datadate'] = format_datadate

        fields = ''
        values = ''

        for k, v in storage.items():
            # 值不为空时，写入键值对
            fields += k.strip() + ','

            if type(v) == str:
                values += '"%s"' % v.strip() + ','
            elif type(v) == datetime.datetime:
                values += '"%s"' % str(v) + ','
            else:
                values += str(v) + ','

        fields = fields[:-1] if fields.endswith(',') else fields
        values = values[:-1] if values.endswith(',') else values

        # 列存，将storage存成一条记录,本地数据库
        tablename = target.storage.tablename
        col_save_sql = r"""INSERT INTO {tablename}({fields}) VALUES({values})""".format(
            tablename=tablename, fields=fields, values=values).replace('"', "'")

        # SQL Server update操作的sql不同
        if 'sql_server' in settings.DATABASES['default']['ENGINE']:
            col_save_sql = r"""INSERT INTO {db}.dbo.{tablename}({fields}) VALUES({values})""".format(
                tablename=tablename, fields=fields, values=values,
                db=settings.DATABASES['default']['NAME']).replace('"', "'")

        logger.info('列存：%s' % col_save_sql)

        db_update = SeveralDBQuery(pro_db_engine, db_info)
        ret = db_update.update(col_save_sql)
        db_update.close()
        result = ret
        if not result:
            error = db_update.error
        else:
            # 列存推送
            result, error = self.push_data(target, storage, result=result, error=error)

        return {"result": result, "error": error}

    def get_col_data(self, target_list, time):

        if target_list:
            storage = OrderedDict()

            for target in target_list:
                result = Extract.getDataFromSource(target, time)
                result_list = result["result"]
                result_error = result["error"]
                if result_error:
                    take_notes(self.source_id, self.app_id, self.cycle_id, result_error)

                # 存表
                storagefields = target.storagefields
                storagefields_list = storagefields.split(',')
                if result_list:
                    result = result_list[0]
                    for num, rt in enumerate(result):
                        storage[storagefields_list[num]] = rt
            if storage:
                # 保存数据
                save_result = self.save_col_data(target_list[0], time, storage)
                saveresult = save_result["result"]
                saveerror = save_result["error"]
                if saveerror:
                    take_notes(self.source_id, self.app_id, self.cycle_id, saveerror)
                if saveresult:
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False

    def format_date(date, pre_format, return_type='str'):
        # D代表取数时刻， < br >
        # DS代表当天0点， < br >
        # DE代表当天24点， < br >
        # L代表昨天同时刻， < br >
        # LDS代表昨天0点， < br >
        # LDE代表昨天24点， < br >
        # MS代表月初， < br >
        # ME代表月末， < br >
        # LMS代表上月初， < br >
        # LME代表上月末， < br >
        # SS代表季初， < br >
        # SE代表季末， < br >
        # LSS代表上季初， < br >
        # LSE代表上季末， < br >
        # HS代表半年初， < br >
        # HE代表半年末， < br >
        # LHS代表上个半年初， < br >
        # LHE代表上个半年末， < br >
        # YS代表年初， < br >
        # YE代表年末， < br >
        # LYS代表去年年初， < br >
        # LYE代表去年末 < br >

        # 匹配出时间点/格式

        cond = pre_format.strip().replace('<#', '').replace('#>', '')

        # 时间点
        newdate = date
        if cond == "D":
            newdate = date
        if cond == "DS":
            newdate = datetime.datetime.strptime('{:%Y-%m-%d}'.format(newdate), '%Y-%m-%d')
        if cond == "DE":
            newdate = datetime.datetime.strptime('{:%Y-%m-%d}'.format(newdate), '%Y-%m-%d') + datetime.timedelta(days=1)
        if cond == "L":
            newdate = date + datetime.timedelta(days=-1)
        if cond == "LDS":
            newdate = datetime.datetime.strptime('{:%Y-%m-%d}'.format(newdate), '%Y-%m-%d') + datetime.timedelta(
                days=-1)
        if cond == "LDE":
            newdate = datetime.datetime.strptime('{:%Y-%m-%d}'.format(newdate), '%Y-%m-%d')

        date = datetime.datetime.strptime('{:%Y-%m-%d}'.format(newdate), '%Y-%m-%d')
        if cond == "MS":
            newdate = date.replace(day=1)
        if cond == "ME":
            year = date.year
            month = date.month
            a, b = calendar.monthrange(year, month)  # a,b——weekday的第一天是星期几（0-6对应星期一到星期天）和这个月的所有天数
            newdate = datetime.datetime(year=year, month=month, day=b)
        if cond == "LME":
            date_now = date.replace(day=1)
            newdate = date_now + datetime.timedelta(days=-1)
        if cond == "LMS":
            date_now = date.replace(day=1)
            date_now = date_now + datetime.timedelta(days=-1)
            newdate = datetime.datetime(date_now.year, date_now.month, 1)
        if cond == "YS":
            newdate = date.replace(month=1, day=1)
        if cond == "YE":
            newdate = date.replace(month=12, day=31)
        if cond == "LYS":
            newdate = date.replace(month=1, day=1)
            newdate = newdate + datetime.timedelta(days=-1)
            newdate = datetime.datetime(newdate.year, 1, 1)
        if cond == "LYE":
            newdate = date.replace(month=1, day=1)
            newdate = newdate + datetime.timedelta(days=-1)
        if cond == "SS":
            month = (date.month - 1) - (date.month - 1) % 3 + 1
            newdate = datetime.datetime(date.year, month, 1)
        if cond == "SE":
            month = (date.month - 1) - (date.month - 1) % 3 + 1
            if month == 10:
                newdate = datetime.datetime(date.year + 1, 1, 1) + datetime.timedelta(days=-1)
            else:
                newdate = datetime.datetime(date.year, month + 3, 1) + datetime.timedelta(days=-1)
        if cond == "LSS":
            month = (date.month - 1) - (date.month - 1) % 3 + 1
            newdate = datetime.datetime(date.year, month, 1)
            newdate = newdate + datetime.timedelta(days=-1)
            newdate = datetime.datetime(newdate.year, newdate.month - 2, 1)
        if cond == "LSE":
            month = (date.month - 1) - (date.month - 1) % 3 + 1  # 10
            newdate = datetime.datetime(date.year, month, 1)
            newdate = newdate + datetime.timedelta(days=-1)
        if cond == "HS":
            month = (date.month - 1) - (date.month - 1) % 6 + 1
            newdate = datetime.datetime(date.year, month, 1)
        if cond == "HE":
            month = (date.month - 1) - (date.month - 1) % 6 + 1
            if month == 7:
                newdate = datetime.datetime(date.year + 1, 1, 1) + datetime.timedelta(days=-1)
            else:
                newdate = datetime.datetime(date.year, month + 6, 1) + datetime.timedelta(days=-1)
        if cond == "LHS":
            month = (date.month - 1) - (date.month - 1) % 6 + 1
            newdate = datetime.datetime(date.year, month, 1)
            newdate = newdate + datetime.timedelta(days=-1)
            newdate = datetime.datetime(newdate.year, newdate.month - 5, 1)
        if cond == "LHE":
            month = (date.month - 1) - (date.month - 1) % 6 + 1
            newdate = datetime.datetime(date.year, month, 1)
            newdate = newdate + datetime.timedelta(days=-1)

        date_init = '' if return_type == 'str' else None

        if return_type == 'str':
            date_init = '{:%Y-%m-%d}'.format(newdate)
        if return_type == 'timestamp':
            date_init = newdate

        return date_init

    def record_exception_data(self, target):
        """
        记录异常数据
        :param target:
        :return:
        """
        try:
            exception_data = ExceptionData()
            exception_data.target = target
            exception_data.app_id = target.adminapp_id
            exception_data.cycle_id = target.cycle_id
            exception_data.source_id = target.source_id
            exception_data.extract_error_time = datetime.datetime.now()
            exception_data.save()
        except Exception as e:
            take_notes(self.source_id, self.app_id, self.cycle_id, '记录异常数据失败：%s' % e)

    def supplement_exception_data(self):
        process_monitor = ProcessMonitor.objects.exclude(state='9')

        for pm in process_monitor:
            app_id = pm.app_admin_id
            source_id = pm.source_id
            cycle_id = pm.cycle_id

            if all([app_id, source_id, cycle_id]):
                # 进程 > 异常补取 > 行：target直接补取；列：集合所有target_list
                exception_data = ExceptionData.objects.exclude(state='9').filter(app_id=app_id, source_id=source_id,
                                                                                 cycle_id=cycle_id)
                copy_exception_data = copy.deepcopy(exception_data)

                for ed in exception_data:
                    storage = ed.target.storage
                    if storage:
                        storage_type_name = get_dict_name(storage.storagetype)

                        if storage_type_name == '行':
                            if ed.supplement_times < 10:
                                if not self.get_row_data(ed.target, ed.extract_error_time):
                                    ed.supplement_times += 1
                                    ed.last_supplement_time = datetime.datetime.now()
                                    ed.save()
                                else:
                                    ed.state = '9'
                                    ed.save()
                            else:
                                pass
                        elif storage_type_name == '列':
                            col_ordered_data = copy_exception_data.filter(target__storage=storage,
                                                                          target__storagetag=ed.target.storagetag)

                            target_list = []
                            for cod in col_ordered_data:
                                target_list.append(cod.target)

                            if not self.get_col_data(target_list, ed.extract_error_time):
                                for cod in col_ordered_data:
                                    cod.supplement_times += 1
                                    cod.last_supplement_time = datetime.datetime.now()
                                    cod.save()
                            else:
                                for cod in col_ordered_data:
                                    cod.state = '9'
                                    cod.save()
                            # 剔除
                            copy_exception_data = copy_exception_data.exclude(target__storage=storage,
                                                                              target__storagetag=ed.target.storagetag)
                        else:
                            take_notes(self.source_id, self.app_id, self.cycle_id,
                                       'Extract >> supplement_exception_data() >> %s' % 'storage_storagetag为空。')

    def push_data(self, target, storage, result=True, error=""):
        """
        推送数据至其他数据库
        """
        result = result
        error = error
        if_push = target.if_push
        if if_push == "1":
            push_config = target.push_config
            try:
                push_config = eval(push_config)
            except:
                result = False
                error = '未配置推送字段。'
            else:
                constraint_fields = push_config['constraint_fields']
                dest_table = push_config['dest_table']
                origin_source = push_config['origin_source']
                origin_fields = push_config['origin_fields']
                dest_fields = push_config['dest_fields']
                try:
                    origin_source = int(origin_source)
                    push_source = Source.objects.get(id=origin_source)
                except Exception as e:
                    result = False
                    error = '推送数据源不存在: {0}。'.format(e)
                else:
                    push_source_connection = push_source.connection
                    push_source_name = push_source.name
                    push_source_db_name = ''
                    try:
                        push_source_connection = eval(push_source_connection)
                        if type(push_source_connection) == list:
                            push_source_connection = push_source_connection[0]
                    except Exception as e:
                        pass
                    else:
                        push_source_db_name = push_source_connection['db']

                    # 推送的SQL
                    #   根据 push_source_name 是否 SQL Server区分
                    #   根据 约束字段的值 是否在对方数据库中存在
                    #       如果存在，返回ID更新；
                    #       如果不存在，新增;
                    condition = "WHERE "
                    set_value = ''
                    create_fields = ''
                    create_values = ''
                    for k, v in storage.items():
                        k = k.strip()
                        # 约束字段
                        if k in constraint_fields:
                            if type(v) == str:
                                condition += "{k}='{v}' AND ".format(k=k, v=v.strip())
                            elif type(v) == datetime.datetime:
                                condition += "{k}='{v}' AND ".format(k=k, v=str(v))
                            else:
                                condition += "{k}={v} AND ".format(k=k, v=str(v))

                        # 更新字段 
                        #     从获取到的字段对应推送字段，取得value值，重新构造目标字段与value的关系
                        # 推送字段索引
                        try:
                            push_index = origin_fields.index(k)
                        except Exception as e:
                            pass
                        else:
                            dest_field = dest_fields[push_index]
                            create_fields += dest_field.strip() + ','
                            if type(v) == str:
                                set_value += "{k}='{v}' ,".format(k=dest_field, v=v.strip())
                                create_values += '"%s"' % v.strip() + ','
                            elif type(v) == datetime.datetime:
                                set_value += "{k}='{v}' ,".format(k=dest_field, v=str(v))
                                create_values += "'%s'" % str(v) + ','
                            else:
                                set_value += "{k}='{v}' ,".format(k=dest_field, v=str(v))
                                create_values += str(v) + ','

                    if condition.endswith(' AND '):
                        condition = condition[:-5]
                    if set_value.endswith(' ,'):
                        set_value = set_value[:-2]

                    # 处理单双引号
                    set_value = set_value.replace('"', "'")
                    create_values = create_values.replace('"', "'")
                    condition = condition.replace('"', "'")

                    create_fields = create_fields[:-1] if create_fields.endswith(',') else create_fields
                    create_values = create_values[:-1] if create_values.endswith(',') else create_values

                    push_db = SeveralDBQuery(push_source_name, push_source_connection)
                    # 修改/新增
                    update_id = None
                    if constraint_fields:
                        check_exist_sql = """SELECT id from {dest_table} {condition}""".format(dest_table=dest_table,
                                                                                               condition=condition)
                        if push_source_name == "SQL Server":
                            check_exist_sql = """SELECT id from {db}.dbo.{dest_table} {condition}""".format(
                                db=push_source_db_name, dest_table=dest_table, condition=condition
                            )
                        logger.info('检查是否存在约束字段的数据: %s' % check_exist_sql)
                        push_db.fetch_all(check_exist_sql)
                        check_ret = push_db.result
                        if check_ret:
                            update_id = check_ret[-1][0]

                    if update_id:
                        try:
                            # 修改
                            push_update_sql = """UPDATE {dest_table} SET {set_value} WHERE id={update_id}""".format(
                                dest_table=dest_table, set_value=set_value, update_id=update_id
                            )
                            if push_source_name == "SQL Server":
                                push_update_sql = """UPDATE {db}.dbo.{dest_table} SET {set_value} WHERE id={update_id}""".format(
                                    db=push_source_db_name, dest_table=dest_table, set_value=set_value,
                                    update_id=update_id
                                )
                            logger.info('Target~%d 推送SQL:%s' % (target.id, push_update_sql))
                            push_update_ret = push_db.update(push_update_sql)
                        except Exception as e:
                            logger.info('数据推送失败：%s' % e)
                            return False, str(e)
                    else:
                        try:
                            # 新增
                            push_create_sql = """INSERT INTO {dest_table}({fields}) VALUES({values})""".format(
                                dest_table=dest_table, fields=create_fields, values=create_values
                            )
                            if push_source_name == "SQL Server":
                                push_create_sql = """INSERT INTO {db}.dbo.{dest_table}({fields}) VALUES({values})""".format(
                                    db=push_source_db_name, dest_table=dest_table, fields=create_fields,
                                    values=create_values
                                )
                            logger.info('Target~%d 推送SQL:%s' % (target.id, push_create_sql))
                            push_update_ret = push_db.update(push_create_sql)
                        except Exception as e:
                            logger.info('数据推送失败：%s' % e)
                            return False, str(e)
                    if not push_update_ret:
                        result = False
                        error = '推送数据失败: {0}'.format(push_db.error)

                    push_db.close()
        return result, error

    def run(self):
        # 补取()
        # 启动定时器，每分钟执行一次
        self.supplement()
        self.set_timer()


def take_notes(source_id, app_id, cycle_id, content):
    """
    记录日志
    :param info:
    :return:
    """
    try:
        source_id = int(source_id)
        app_id = int(app_id)
        cycle_id = int(cycle_id)
    except:
        pass
    else:
        log_info = LogInfo()
        log_info.source_id = source_id
        log_info.app_id = app_id
        log_info.cycle_id = cycle_id
        log_info.content = content
        log_info.create_time = datetime.datetime.now()
        log_info.save()


def run_process(process_id, targets=None):
    """
    后台进程
    :param process_id: 进程ID
    :param targets: 选中指标列表
    :return:
    """
    # 取数 *****************************************************
    pid = os.getpid()
    logger.info('此次进程pid: %d ' % pid)
    if process_id:
        process_id = int(process_id)

        # 实际
        try:
            update_pm = ProcessMonitor.objects.get(id=process_id)
        except Exception as e:
            logger.info('run_process() >> %s' % e)
        else:
            if targets:
                # 对选中指标列表进行补取
                targets = [i for i in targets.split('^') if i]
                app_id = update_pm.app_admin_id
                source_id = update_pm.source_id
                cycle_id = update_pm.cycle_id
                # 取数进程
                extract = Extract(app_id, source_id, cycle_id)
                # 补取进程对应的主进程必须已运行过
                sp = SupplementProcess.objects.exclude(state='9').filter(primary_process_id=process_id).last()
                if sp:
                    # 保存当前补取进程ID
                    sp.p_id = pid
                    sp.save()
                    # 选择补取的时间区间
                    start_time = sp.start_time
                    end_time = sp.end_time
                    # start_time加上一分钟，低于end_time继续循环补取，超过则停止
                    tmp_time = datetime.datetime.now()
                    t = 0
                    while True:
                        t += 1
                        # 一分钟更新一次 更新时间、进度时间
                        if (datetime.datetime.now() - tmp_time).total_seconds() > 60 or t == 1:
                            sp.update_time = datetime.datetime.now()
                            sp.progress_time = start_time
                            sp.save()
                            tmp_time = datetime.datetime.now()

                        start_time = start_time + datetime.timedelta(minutes=1)
                        # 判断周期, 取数
                        # 判断当前时间是否符合周期规则
                        cycle_rule = update_pm.cycle
                        if cycle_rule:
                            schedule_type = cycle_rule.schedule_type
                            minute, hour, day_of_week, day_of_month = None, None, None, None
                            try:
                                minute = int(cycle_rule.minute)
                            except:
                                pass
                            try:
                                hour = int(cycle_rule.hour)
                            except:
                                pass
                            try:
                                day_of_week = int(cycle_rule.day_of_week)
                            except:
                                pass
                            try:
                                day_of_month = int(cycle_rule.day_of_month)
                            except:
                                pass

                            # 当前时间
                            now_minute = start_time.minute
                            now_hour = start_time.hour
                            now_weekday = start_time.weekday()
                            now_day = start_time.day

                            if now_hour == hour and now_minute == minute:
                                # 每日/每周/每月
                                if schedule_type == 1:
                                    extract._get_data(start_time, targets)
                                if schedule_type == 2:
                                    # 判断一周第几天
                                    if now_weekday == day_of_week:
                                        extract._get_data(start_time, targets)
                                if schedule_type == 3:
                                    # 判断一月第几天
                                    if now_day == day_of_month:
                                        extract._get_data(start_time, targets)

                        if start_time > end_time:
                            time.sleep(2)
                            # 补取结束，修改状态(1 启动成功 0 补取完成 2 补取失败)
                            sp.p_state = "0"
                            sp.save()

                            break

                def check_py_exists(pid):
                    process = None
                    try:
                        pid = int(pid)
                        if psutil.pid_exists(pid):
                            process = psutil.Process(pid=pid)
                            if 'python.exe' not in process.name():
                                process = None
                    except:
                        pass

                    return process

                sp = check_py_exists(pid)
                if sp:
                    sp.terminate()

            else:
                # 取数
                update_pm.create_time = datetime.datetime.now()
                update_pm.p_id = pid
                update_pm.save()

                app_id = update_pm.app_admin_id
                source_id = update_pm.source_id
                cycle_id = update_pm.cycle_id

                # 根据数据源类型来判断进程
                try:
                    source = Source.objects.get(id=source_id)
                except Source.DoesNotExist as e:
                    pass
                else:
                    process_type = source.type
                    if process_type == '1':
                        # 数据补取
                        while True:
                            try:
                                # 补取
                                extract = Extract(app_id, source_id, cycle_id)
                                extract.supplement_exception_data()

                                logger.info('异常数据补取结束。')
                            except Exception as e:
                                logger.info('数据补取失败：%s' % e)

                            time.sleep(60 * 60 * 0.5)  # 半小时对所有异常取数记录进行补取一次，10次补取失败作罢，历时5小时
                    elif process_type == '2':
                        while True:
                            try:
                                # 数据清理：根据存储配置中的数据保留周期，定时去删除表中的过期数据
                                now_time = datetime.datetime.now()
                                # 遍历所有storage
                                storages = Storage.objects.exclude(state='9')
                                for storage in storages:
                                    valid_time = get_dict_name(storage.validtime)
                                    table_name = storage.tablename

                                    aft_time = None
                                    if valid_time == '一年':
                                        aft_time = now_time + datetime.timedelta(days=-365)
                                    elif valid_time == '一个月':
                                        aft_time = now_time + datetime.timedelta(days=-30)
                                    else:
                                        # # 永久：测试用，如果为永久暂时保留2天内的数据
                                        # aft_time = now_time + datetime.timedelta(days=-2)
                                        pass

                                    if aft_time:
                                        clean_sql = r"""DELETE FROM {table_name} WHERE savedate < '{savedate:%Y-%m-%d %H:%M:%S}'""".format(
                                            table_name=table_name, savedate=aft_time)

                                        if 'sql_server' in settings.DATABASES['default']['ENGINE']:
                                            clean_sql = r"""DELETE FROM {db}.dbo.{table_name} WHERE savedate < '{savedate:%Y-%m-%d %H:%M:%S}'""".format(
                                                table_name=table_name, savedate=aft_time,
                                                db=settings.DATABASES['default']['NAME'])

                                        db_update = SeveralDBQuery(pro_db_engine, db_info)
                                        logger.info(
                                            '时间 [{savedate:%Y-%m-%d %H:%M:%S}] 前数据清理成功。'.format(savedate=aft_time))
                                        ret = db_update.update(clean_sql)
                                        db_update.close()

                                        if not ret:
                                            logger.info('数据清理失败：SQL执行出错。')
                            except Exception as e:
                                logger.info('数据清理失败：%s' % e)

                            time.sleep(60 * 60 * 24)  # 定时1日
                    elif process_type == '3':
                        # 数据服务
                        pass
                    elif process_type == '4':
                        # 短信服务
                        pass
                    else:
                        # 取数进程
                        extract = Extract(app_id, source_id, cycle_id)
                        extract.run()
    else:
        logger.info('run_process() >> %s' % '传入参数有误。')


if __name__ == '__main__':
    logger.info('======================================================================================')
    logger.info('======================================================================================')
    if len(sys.argv) == 2:
        # 后台定时任务进程
        logger.info('进程启动。')

        run_process(sys.argv[1])
    elif len(sys.argv) == 3:
        # 选择指标补取进程
        logger.info('进程启动。')

        run_process(sys.argv[1], sys.argv[2])
    else:
        logger.info('脚本未传参。')
