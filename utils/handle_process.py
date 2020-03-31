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
# 引入C#脚本
import clr

clr.AddReference('PIApp')
from PIApp import *
# 使用ORM
import sys
from django.core.wsgi import get_wsgi_application

# 获取django路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.extend([r'%s' % BASE_DIR, ])
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ZDDC.settings")
application = get_wsgi_application()
from datacenter.models import *
from django.db.models import Q
from django.conf import settings

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
    def __init__(self, db_type, credit):
        # [{"host":"192.168.1.66","user":"root","passwd":"password","db":"datacenter"}]
        self.db_type = db_type.replace(' ', '').upper()
        self.connection = None

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
            logger.info('SeveralDBQuery >> __init__() >> 数据库连接失败: %s。' % e)
        else:
            if not self.connection:
                logger.info('SeveralDBQuery >> __init__() >> 数据库未连接。')

    def fetch_one(self, fetch_sql):
        result = None
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(fetch_sql)
                result = cursor.fetchone()
        except Exception as e:
            logger.info("数据查询失败：%s" % e)
        return result

    def fetch_all(self, fetch_sql):
        logger.info('查询SQL：%s' % fetch_sql)
        result = []
        try:
            if self.db_type == 'ORACLE':
                curs = self.connection.cursor()
                curs.execute(fetch_sql)
                result = curs.fetchall()
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
                            result.append(tmp_result)

                    else:
                        result = cursor.fetchall()
        except Exception as e:
            logger.info("数据查询失败：%s" % e)

        return result

    def update(self, update_sql):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(update_sql)
                self.connection.commit()
        except Exception as e:
            logger.info("数据插入失败：%s" % e)

    def close(self):
        if self.connection:
            self.connection.close()


class Extract(object):
    """
    先补取，后定时取数
    """

    def __init__(self, app_id, source_id, circle_id):
        self.app_id = app_id
        self.source_id = source_id
        self.circle_id = circle_id
        self.pm = None
        try:
            self.pm = ProcessMonitor.objects.get(app_admin_id=self.app_id, source_id=self.source_id,
                                                 cycle_id=self.circle_id)
        except ProcessMonitor.DoesNotExist as e:
            logger.info('Extract >> __init__() >> %s' % e)
        else:
            if not self.pm:
                logger.info('Extract >> supplement() >> 该进程不存在，取数进程启动失败。')

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
            logger.info('Extract >> supplement() >> 首次取数，不进行补取。')

        # 补取过程也消耗时间，再次判断进行补取:先把秒数抹掉再比较
        aft_last_time = self.pm.last_time

        try:
            aft_last_time = datetime.datetime.strptime('{:%Y-%m-%d %H:%M}'.format(aft_last_time), '%Y-%m-%d %H:%M')
            now_time = datetime.datetime.strptime('{:%Y-%m-%d %H:%M}'.format(datetime.datetime.now()), '%Y-%m-%d %H:%M')
        except Exception as e:
            logger.info('Extract >> supplement() >> %s' % e)
        else:
            try:
                delta_time = (now_time - aft_last_time).total_seconds()
            except Exception as e:
                logger.info('Extract >> supplement() >> %s' % e)
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
        circle_rule = self.pm.cycle
        if circle_rule:
            schedule_type = circle_rule.schedule_type
            minute = circle_rule.minute
            hour = circle_rule.hour
            day_of_week = circle_rule.day_of_week
            day_of_month = circle_rule.day_of_month

            # 当前时间
            now_minute = now_time.minute
            now_hour = now_time.hour
            now_weekday = str(now_time.weekday())
            now_day = str(now_time.day)

            # 测试5秒取
            # self._get_data(now_time)
            # time.sleep(5)
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

    def _get_data(self, now_time):
        ordered_targets = Target.objects.filter(adminapp_id=self.app_id, source_id=self.source_id,
                                                cycle_id=self.circle_id).exclude(state='9').order_by('storage_id',
                                                                                                     'storagetag')
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

                    if self.get_col_data(col_ordered_targets, now_time):
                        # 剔除
                        copy_ordered_targets = copy_ordered_targets.exclude(storage=storage,
                                                                            storagetag=o_target.storagetag)
                    else:
                        for cot in col_ordered_targets:
                            self.record_exception_data(cot)
                else:
                    logger.info('Extract >> _get_data() >> %s' % 'storage_storagetag为空。')

    @staticmethod
    def get_data_from_pi(source_content, source_connection):
        """
        从PI中取数据
            type: avg, max, min, delta, history, real
            # 解析PI的数据源内容
            # tmp = {
            #     'tag': '',
            #     'type': '',
            #     'start_time': '',
            #     'end_time': ''
            # }
        :return:
        """
        result_list = []
        try:
            source_content = eval(source_content)
        except Exception as e:
            logger.info('Extract >> get_row_data() >> PI数据源内容填写有误：%s' % e)
        else:
            if type(source_content) == dict:
                tag, operate, start_time, end_time = '', '', None, None
                if 'tag' in source_content.keys():
                    tag = source_content['tag']
                if 'start_time' in source_content.keys():
                    start_time = source_content['start_time']
                if 'end_time' in source_content.keys():
                    end_time = source_content['end_time']
                if 'type' in source_content.keys():
                    operate = source_content['type'].upper()

                curvalue = None
                status = 1
                try:
                    conn = source_connection['host']

                    if operate == 'DATATABLE':
                        curvalue = ManagePI.ReadDatetableFromPI(conn, tag, start_time, end_time, 100)
                    else:
                        if operate == 'REAL':
                            curvalue = json.loads(ManagePI.ReadRealValueFromPI(conn, tag))
                        elif operate == 'HISTORY':
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
                        result_list = [[curvalue['value']]]
                    elif type(curvalue) == list:
                        pass
                    else:
                        pass
                else:
                    logger.info('Extract >> get_row_data() >> PI数据获取失败：%s' % curvalue)

            else:
                logger.info('Extract >> get_row_data() >> PI数据源内容填写非JSON格式')

            return result_list

    def get_row_data(self, target, time):
        # storagefields有4个特例，
        # 1.id，id字段不需要配置，storage表必有id字段并自增长
        # 2.target_id,target_id字段不需要配置,代码中强制保存index.id到storage的target_id字段
        # 3.savedate,savedate字段不需要配置,代码中强制保存time到storage的savedate字段
        # 4.datadate，配置时需放在普通字段之后，datadate格式如<#DATADATE:m:S#>，参考source_content中的时间格式，将time格式化后再转成日期格式保存
        # 获取行数据
        source_content = target.source_content
        storagefields = target.storagefields
        storagefields_list = storagefields.split(',')

        # 匹配出<#DATE:m:L#>
        date_com = re.compile('<#.*?#>')
        pre_format_list = date_com.findall(source_content)

        if pre_format_list:
            format_date = self.format_date(time, pre_format_list[0])

            # 格式化后的SQL
            source_content = source_content.replace(pre_format_list[0], format_date)

        # datadate
        pre_datadate_format_list = date_com.findall(storagefields)

        format_datadate = self.format_date(time, pre_datadate_format_list[0],
                                           return_type='timestamp') if pre_datadate_format_list else None

        result_list = []

        source = target.source
        source_type_name = ''
        if source:
            source_type = source.sourcetype  # Oracle/SQL Server
            source_type_name = get_dict_name(source_type)

            source_connection = ''
            try:
                source_connection = eval(source.connection)
                if type(source_connection) == list:
                    source_connection = source_connection[0]
            except Exception as e:
                logger.info('Extract >> get_row_data() >> 数据源配置认证信息错误：%s' % e)
            else:
                if source_type_name == 'PI':
                    result_list = Extract.get_data_from_pi(source_content, source_connection)
                else:
                    db_query = SeveralDBQuery(source_type_name, source_connection)
                    result_list = db_query.fetch_all(source_content)
                    db_query.close()

        if not result_list:
            return False
        else:
            for result in result_list:
                storage = OrderedDict()

                for num, rt in enumerate(result):
                    storage[storagefields_list[num]] = rt

                storage["savedate"] = time
                storage['target_id'] = target.id
                if 'DATADATE' in storagefields:
                    # storage['datadate']
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

                logger.info('行：%s' % row_save_sql)
                try:
                    db_update = SeveralDBQuery(pro_db_engine, db_info)
                    db_update.update(row_save_sql)
                    db_update.close()
                except Exception as e:
                    logger.info('数据更新失败： %s' % e)
                    return False
            return True

    def get_col_data(self, target_list, time):
        storage = OrderedDict()
        storage["savedate"] = time
        # 格式化时间<datadate:MS>  storage['datadate'] 

        date_com = re.compile('<#.*?#>')

        if target_list:
            source_type_name = ''
            # datadate
            if 'DATADATE' in target_list[0].storagefields:
                pre_datadate_format_list = date_com.findall(target_list[0].storagefields)
                format_datadate = self.format_date(time, pre_datadate_format_list[0],
                                                   return_type='timestamp') if pre_datadate_format_list else None
                storage['datadate'] = format_datadate

            # 获取列数据
            for target in target_list:
                source_content = target.source_content

                # 匹配出<#DATE:m:L#>
                pre_format_list = date_com.findall(source_content)

                format_date = self.format_date(time, pre_format_list[0] if pre_format_list else '')

                # 格式化后的SQL
                source_content = source_content.replace(pre_format_list[0],
                                                        format_date) if pre_format_list else source_content

                result_list = []

                source = target.source
                if source:
                    source_type = source.sourcetype  # Oracle/SQL Server
                    source_type_name = get_dict_name(source_type)

                    source_connection = ''
                    try:
                        source_connection = eval(source.connection)
                        if type(source_connection) == list:
                            source_connection = source_connection[0]
                    except Exception as e:
                        logger.info('Extract >> get_row_data() >> 数据源配置认证信息错误：%s' % e)

                    if source_type_name == 'PI':
                        result_list = Extract.get_data_from_pi(source_content, source_connection)
                    else:
                        db_query = SeveralDBQuery(source_type_name, source_connection)
                        result_list = db_query.fetch_all(source_content)
                        db_query.close()

                # 存表
                storagefields = target.storagefields
                storagefields_list = storagefields.split(',')
                if result_list:
                    result = result_list[0]

                    for num, rt in enumerate(result):
                        storage[storagefields_list[num]] = rt

            fields = ''
            values = ''

            if storage:
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
                tablename = target_list[0].storage.tablename
                col_save_sql = r"""INSERT INTO {tablename}({fields}) VALUES({values})""".format(tablename=tablename,
                                                                                                fields=fields,
                                                                                                values=values).replace(
                    '"', "'")

                # SQL Server update操作的sql不同
                if 'sql_server' in settings.DATABASES['default']['ENGINE']:
                    col_save_sql = r"""INSERT INTO {db}.dbo.{tablename}({fields}) VALUES({values})""".format(
                        tablename=tablename, fields=fields, values=values,
                        db=settings.DATABASES['default']['NAME']).replace('"', "'")

                logger.info('列存：%s' % col_save_sql)
                try:
                    db_update = SeveralDBQuery(pro_db_engine, db_info)
                    db_update.update(col_save_sql)
                    db_update.close()
                except Exception as e:
                    logger.info('数据更新失败： %s' % e)
                    return False
                else:
                    return True
            else:
                return False
        else:
            return False

    def format_date(self, date, pre_format, return_type='str'):
        # {
        # "D": "当前", "L": "前一天", "MS": "月初", "ME": "月末", "LMS": "上月初", "LME": "上月末", "SS": "季初", "SE": "季末",
        # "LSS": "上季初", "LSE": "上季末", "HS": "半年初", "HE": "半年末", "LHS": "前个半年初", "LHE": "前个半年末", "YS": "年初",
        # "YE": "年末", "LYS": "去年初", "LYE": "去年末"
        # }

        # 匹配出时间点/格式
        com = re.compile('.*?:([a-z A-Z]+):([a-z A-Z]+).*?')

        format_params = com.findall(pre_format)

        time_format, cond = format_params[0] if format_params else ['', '']

        # 时间点
        newdate = date  # if cond == "D":
        if cond == "L":
            newdate = date + datetime.timedelta(days=-1)
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
        # 格式
        if return_type == 'str':
            if time_format == 's':
                date_init = '{:%Y-%m-%d %H:%M:%S}'.format(newdate)
            if time_format == 'mi':
                date_init = '{:%Y-%m-%d %H:%M}'.format(newdate)
            if time_format == 'h':
                date_init = '{:%Y-%m-%d %H}'.format(newdate)
            if time_format == 'd':
                date_init = '{:%Y-%m-%d}'.format(newdate)
            if time_format == 'm':
                date_init = '{:%Y-%m}'.format(newdate)
            if time_format == 'y':
                date_init = '{:%Y}'.format(newdate)
        if return_type == 'timestamp':
            if time_format == 's':
                date_init = datetime.datetime.strptime('{:%Y-%m-%d %H:%M:%S}'.format(newdate), '%Y-%m-%d %H:%M:%S')
            if time_format == 'mi':
                date_init = datetime.datetime.strptime('{:%Y-%m-%d %H:%M}'.format(newdate), '%Y-%m-%d %H:%M')
            if time_format == 'h':
                date_init = datetime.datetime.strptime('{:%Y-%m-%d %H}'.format(newdate), '%Y-%m-%d %H')
            if time_format == 'd':
                date_init = datetime.datetime.strptime('{:%Y-%m-%d}'.format(newdate), '%Y-%m-%d')
            if time_format == 'm':
                date_init = datetime.datetime.strptime('{:%Y-%m}'.format(newdate), '%Y-%m')
            if time_format == 'y':
                date_init = datetime.datetime.strptime('{:%Y}'.format(newdate), '%Y')

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
            logger.info('记录异常数据失败：%s' % e)

    def supplement_exception_data(self):
        process_monitor = ProcessMonitor.objects.exclude(state='9')

        for pm in process_monitor:
            app_id = pm.app_admin_id
            source_id = pm.source_id
            circle_id = pm.cycle_id

            if all([app_id, source_id, circle_id]):
                # 进程 > 异常补取 > 行：target直接补取；列：集合所有target_list
                exception_data = ExceptionData.objects.exclude(state='9').filter(app_id=app_id, source_id=source_id,
                                                                                 cycle_id=circle_id)
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
                                # 剔除
                                copy_exception_data = copy_exception_data.exclude(target__storage=storage,
                                                                                  target__storagetag=ed.target.storagetag)
                                for cod in col_ordered_data:
                                    cod.state = '9'
                                    cod.save()
                        else:
                            logger.info('Extract >> supplement_exception_data() >> %s' % 'storage_storagetag为空。')

    def run(self):
        # 补取()
        # 启动定时器，每分钟执行一次
        self.supplement()
        self.set_timer()


def run_process(process_id, processcon, targets):
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
            update_pm.create_time = datetime.datetime.now()
            update_pm.p_id = pid
            update_pm.save()

            app_id = update_pm.app_admin_id
            source_id = update_pm.source_id
            circle_id = update_pm.cycle_id

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
                        # 补取
                        extract = Extract(app_id, source_id, circle_id)
                        extract.supplement_exception_data()

                        time.sleep(60 * 60 * 24)  # 定时1日
                elif process_type == '2':
                    while True:
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
                                logger.info('时间 [{savedate:%Y-%m-%d %H:%M:%S}] 前数据清理成功。'.format(savedate=aft_time))
                                # db_update.update(clean_sql)
                                db_update.close()

                        time.sleep(60 * 60 * 24)  # 定时1日
                elif process_type == '3':
                    # 数据服务
                    pass
                elif process_type == '4':
                    # 短信服务
                    pass
                else:
                    # 取数进程
                    extract = Extract(app_id, source_id, circle_id)
                    extract.run()
    else:
        logger.info('run_process() >> %s' % '传入参数有误。')


if len(sys.argv) > 1:
    run_process(sys.argv[1], None, None)
    logger.info('进程启动。')
else:
    logger.info('脚本未传参。')

# db_query = SeveralDBQuery('SQLSERVER', {"host":"127.0.0.1","user":"miaokela","passwd":"Passw0rD","db":"mkl"})
# result_list = db_query.update("INSERT INTO dt.dbo.tmp_table(datadate,formula,target_id) VALUES('2020-02-16 00:00:00.000000','<#1_FDL:d:D>+<FDL:d:D>',36); ")
# # result_list = db_query.fetch_all("SELECT TOP 1000 [id],[target_id],[datadate],[curvalue],[formula],[state] FROM [dt].[dbo].[tmp_table]")
# db_query.close()

# extract = Extract(1, 2, 2)
# target = Target.objects.get(id=9)
# time = datetime.datetime.now()
# extract.get_row_data(target, time)
# # targets = Target.objects.filter(Q(id=8)|Q(id=9))
# # extract.get_col_data(targets, time)

# run_process(12, None, None)  # mysql测试成功1 测试成功2     42, 43
# run_process(11, None, None)  # pi 测试成功1 测试成功2   66, 67
# run_process(10, None, None)  # sqlserver 测试成功1 测试成功2  38,39,40,41
# run_process(13, None, None) # oracle 测试成功1 44, 45

# 数据清理
# run_process(14, None, None)
