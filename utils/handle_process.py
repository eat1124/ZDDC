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
import calendar

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
# logger.info('test')

def getcumulative(target, date, value):
    """
    数据累计
    """
    cumulativemonth = value
    cumulativequarter = value
    cumulativehalfyear = value
    cumulativeyear = value
    lastg_date = datetime.datetime.strptime('2000-01-01', "%Y-%m-%d")
    if target.cycletype == "10":
        lastg_date = date + datetime.timedelta(days=-1)
    if target.cycletype == "11":
        lastg_date = (date.replace(day=1, hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(
            days=-1)).replace(day=1)
    if target.cycletype == "12":
        lastg_date = (date.replace(day=1, hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(
            days=-1)).replace(day=1)
    if target.cycletype == "13":
        lastg_date = (date.replace(day=1, hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(
            days=-1)).replace(day=1)
    if target.cycletype == "14":
        lastg_date = (date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(
            days=-1)).replace(month=1, day=1)

    # all_data = []
    # if target.operationtype == "15":
    #     all_data = Entrydata.objects.exclude(state="9").filter(target=target, datadate=lastg_date)
    # if target.operationtype == "16":
    #     all_data = Extractdata.objects.exclude(state="9").filter(target=target, datadate=lastg_date)
    # if target.operationtype == "17":
    #     all_data = Calculatedata.objects.exclude(state="9").filter(target=target, datadate=lastg_date)
    # if len(all_data) > 0:
    #     cumulativemonth = all_data[0].cumulativemonth + value
    #     cumulativequarter = all_data[0].cumulativequarter + value
    #     cumulativehalfyear = all_data[0].cumulativehalfyear + value
    #     cumulativeyear = all_data[0].cumulativeyear + value
    return {"cumulativemonth": cumulativemonth, "cumulativequarter": cumulativequarter,
            "cumulativehalfyear": cumulativehalfyear, "cumulativeyear": cumulativeyear}


def getextractdata(target):
    """
    数据提取
    """
    curvalue = []

    con = target.source.connection
    con = json.loads(con)
    db = pymysql.connect(con[0]["host"], con[0]["user"], con[0]["passwd"], con[0]["db"])
    cursor = db.cursor()
    strsql = "select " + target.sourcefields + " from " + target.sourcetable + " where " + target.sourceconditions
    cursor.execute(strsql)
    data = cursor.fetchall()
    if len(data) > 0:
        curvalue = data[0][0]

    return curvalue


class SeveralDBQuery(object):
    def __init__(self, db_type, credit):
        # {"host":"192.168.1.66","user":"root","passwd":"password","db":"datacenter"}
        self.db_type = db_type
        self.connection = None

        try:
            if self.db_type == "MySQL":
                import pymysql.cursors

                self.connection = pymysql.connect(host=credit['host'],
                                            user=credit['user'],
                                            password=credit['passwd'],
                                            db=credit['db'],
                                            charset='utf8mb4',
                                            cursorclass=pymysql.cursors.DictCursor)
            if self.db_type == 'Oracle':
                import cx_Oracle

                self.connection = cx_Oracle.connect('{user}/{passwd}@{host}/{db}'.format(
                    user=credit['user'],
                    passwd=credit['passwd'],
                    host=credit['host'],
                    db=credit['db']
                ))
            if self.db_type == 'SQL Server':
                import pymssql

                self.connection = pymssql.connect(
                    host=credit['host'],
                    user=credit['user'],
                    password=credit['passwd'],
                    database=credit['db']
                )
        except Exception as e:
            logger.info('SeveralDBQuery >> __init__() >> 数据库连接失败: %s。' % e)
            exit(0)
        else:
            if not self.connection:
                logger.info('SeveralDBQuery >> __init__() >> 数据库未连接。')
                exit(0)

    def fetch_one(self, fetch_sql):
        result = None
        with self.connection.cursor() as cursor:
            cursor.execute(fetch_sql)
            result = cursor.fetchone()
        return result

    def fetch_all(self, fetch_sql):
        result = []
        with self.connection.cursor() as cursor:
            cursor.execute(fetch_sql)
            result = cursor.fetchall()
        return result

    def update(self, update_sql):
        with self.connection.cursor() as cursor:
            cursor.execute(update_sql)
            self.connection.commit()

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
            self.pm = ProcessMonitor.objects.get(app_admin_id=self.app_id, source_id=self.source_id, cycle_id=self.circle_id)
        except ProcessMonitor.DoesNotExist as e:
            logger.info('Extract >> __init__() >> %s' % e)
        else:
            if not self.pm:
                logger.info('Extract >> supplement() >> 该进程不存在，取数进程启动失败。')
                exit(0)

    def supplement(self):
        # 补取
        start_time = self.pm.last_time

        if start_time:
            end_time = datetime.datetime.now()

            # start_time加上一分钟，低于end_time继续循环补取，超过则停止
            while True:
                one_minute_plus = start_time + datetime.timedelta(minutes=1)
                # 取数
                self.get_data(one_minute_plus)
                if one_minute_plus > end_time:
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
            exit(0)
        else:
            try:
                delta_time = (now_time - aft_last_time).total_seconds()
            except Exception as e:
                logger.info('Extract >> supplement() >> %s' % e)
                exit(0)
            else:
                if delta_time > 60:
                    self.supplement()

    def set_timer(self):
        # 定时器
        while True:
            time_now = datetime.datetime.now()
            
            # 暂时注销
            # self.get_data(time_now)
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

    def _get_data(self, now_time):
        ordered_targets = Target.objects.filter(adminapp_id=self.app_id, source_id=self.source_id, cycle_id=self.circle_id).exclude(state='9').order_by('storage_id', 'storagetag')
        copy_ordered_targets = copy.deepcopy(ordered_targets)
        for o_target in ordered_targets:
            storage = o_target.storage
            if storage:
                # 从DictList中获取
                storage_type_name = ''
                try:
                    dl = DictList.objects.get(id=int(storage.storagetype))
                except Exception as e:
                    logger.info('Extract >> _get_data() >> %s' % e)
                else:
                    storage_type_name = dl.name

                if storage_type_name == '行':
                    self.get_row_data(o_target, now_time)
                    logger.info('获取行数据...')
                elif storage_type_name == '列':
                    col_ordered_targets = copy_ordered_targets.filter(storage=storage, storage__storagetype=storage.storagetype)

                    self.get_col_data(col_ordered_targets, now_time)
                    logger.info('获取列数据')
                    # 剔除
                    copy_ordered_targets = copy_ordered_targets.exclude(storage=storage, storagetype=storage.storagetype)
                else:
                    logger.info('Extract >> _get_data() >> %s' % 'storage_storagetag为空。')
        self.pm.last_time = now_time
        self.pm.save()

    def get_row_data(self, target, time):
        # storagefields有4个特例，
		# 1.id，id字段不需要配置，storage表必有id字段并自增长
		# 2.target_id,target_id字段不需要配置,代码中强制保存index.id到storage的target_id字段
		# 3.savedate,savedate字段不需要配置,代码中强制保存time到storage的savedate字段
		# 4.datadate，配置时需放在普通字段之后，datadate格式如<#DATADATE:m:S#>，参考source_content中的时间格式，将time格式化后再转成日期格式保存
        # 获取行数据
        source_content = target.source_content
        storagefields = target.storagefields
        storagefields_ilst = storagefields.split(',')

        # 匹配出<#DATE:m:L#>
        date_com = re.compile('<.*?>')
        pre_format_list = date_com.findall(source_content)

        if pre_format_list:
            format_date = self.format_date(time, pre_format_list[0])

            # 格式化后的SQL
            source_content = source_content.replace(pre_format_list[0], format_date)

        # datadate
        pre_datadate_format_list = date_com.findall(storagefields)

        format_datadate = self.format_date(time, pre_datadate_format_list[0], return_type='timestamp') if pre_datadate_format_list else None

        result_list = []

        source = target.source
        if source:
            source_type_name = ''
            source_type = source.sourcetype  # Oracle/SQL Server
            source_connection = source.connection

            try:
                dl = DictList.objects.get(id=int(source_type))
            except Exception as e:
                logger.info('Extract >> get_row_data() >> %s' % e)
            else:
                source_type_name = dl.name

            db_query = SeveralDBQuery(source_type_name, source_connection)
            result_list = db_query.fetch_all(source_content)
            db_query.close()

        # 本地数据库信息
        connection = {
            'host': settings.DATABASES['default']['HOST'],
            'user': settings.DATABASES['default']['USER'],
            'passwd': settings.DATABASES['default']['PASSWORD'],
            'db': settings.DATABASES['default']['NAME'],
        }
        db_update = SeveralDBQuery('MySQL', connection)

        for result in result_list:
            storage = {}

            ri = 0
            for rk, rv in result.items():
                storage[storagefields_ilst[ri]] = rv
                ri += 1

            storage["savedate"] = time
            storage['target_id'] = target.id
            if 'DATADATE' in storagefields:
                # storage['datadate'] 
                storage['datadate'] = format_datadate

            fields = ''
            values = ''

            for k,v in storage.items():
                fields += k + ','
                if type(v) == 'int':
                    values += v + ','
                if type(v) == 'str':
                    values += '"%s"' % v + ','

            fields = fields[:-1] if fields.endswith(',') else fields
            values = values[:-1] if values.endswith(',') else values

            tablename = target.storage.tablename
            # 行存
            row_save_sql = """INSERT INTO datacenter_{tablename}({fields}) VALUES({values})""".format(tablename=tablename, fields=fields, values=values)

            # print(row_save_sql)
            # db_update.update(row_save_sql)
        db_update.close()

    def get_col_data(self, target_list, time):
        storage = {}
        storage["savedate"] = time
        # 格式化时间<datadate:MS>  storage['datadate'] 

        date_com = re.compile('<.*?>')
        # datadate
        if 'DATADATE' in target_list[0].storagefields:
            pre_datadate_format_list = date_com.findall(target_list[0].storagefields)
            format_datadate = self.format_date(time, pre_datadate_format_list[0], return_type='timestamp') if pre_datadate_format_list else None
            storage['datadate'] = format_datadate

        # 获取列数据
        for target in target_list:
            source_content = target.source_content

            # 匹配出<#DATE:m:L#>
            date_com = re.compile('<.*?>')
            pre_format_list = date_com.findall(source_content)

            format_date = self.format_date(time, pre_format_list[0] if pre_format_list else '')

            # 格式化后的SQL
            source_content = source_content.replace(pre_format_list[0], format_date) if pre_format_list else source_content

            result_list = []

            source = target.source
            if source:
                source_type_name = ''
                source_type = source.sourcetype  # Oracle/SQL Server
                source_connection = source.connection

                try:
                    dl = DictList.objects.get(id=int(source_type))
                except:
                    logger.info('Extract >> get_col_data() >> %s' % e)
                else:
                    source_type_name = dl.name

                db_query = SeveralDBQuery(source_type_name, source_connection)
                result_list = db_query.fetch_all(source_content)
                db_query.close()

            # 存表
            storagefields = target.storagefields
            storagefields_ilst = storagefields.split(',')
            if result_list:
                result = result_list[0]
                i = 0
                for k, v in result.items():
                    # 字段为target.storagefields
                    storage[storagefields_ilst[i]] = v
                    i += 1

        fields = ''
        values = ''

        for k,v in storage.items():
            fields += k + ','
            if type(v) == 'int':
                values += v + ','
            if type(v) == 'str':
                values += '"%s"' % v + ','

        fields = fields[:-1] if fields.endswith(',') else fields
        values = values[:-1] if values.endswith(',') else values

        # 列存，将storage存成一条记录,本地数据库
        tablename = target_list[0].storage.tablename
        col_save_sql = """INSERT INTO datacenter_{tablename}({fields}) VALUES({values})""".format(tablename=tablename, fields=fields, values=values)
        connection = {
            'host': settings.DATABASES['default']['HOST'],
            'user': settings.DATABASES['default']['USER'],
            'passwd': settings.DATABASES['default']['PASSWORD'],
            'db': settings.DATABASES['default']['NAME'],
        }
        db_update = SeveralDBQuery('MySQL', connection)
        # db_update.update(col_save_sql)
        db_update.close()

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
                newdate = datetime.datetime(date.year+1, 1, 1) + datetime.timedelta(days=-1)
            else:
                newdate = datetime.datetime(date.year, month + 3, 1) + datetime.timedelta(days=-1)
        if cond == "LSS":
            month = (date.month - 1) - (date.month - 1) % 3 + 1
            newdate = datetime.datetime(date.year, month, 1)
            newdate = newdate + datetime.timedelta(days=-1)
            newdate = datetime.datetime(newdate.year, newdate.month - 2, 1)
        if cond == "LSE":
            month = (date.month - 1) - (date.month - 1) % 3 + 1  #10
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

    def run(self):
        # 补取()
	    # 启动定时器，每分钟执行一次

        # 暂时注销
        # self.supplement()
        self.set_timer()


def run_process(process_id, processcon, targets):
    # 取数 *****************************************************
    pid = os.getpid()
    if process_id:
        # for target in targets:
        #     curvalue = getextractdata(target)
        #     if not curvalue:
        #         extractdata = Extractdata()
        #         extractdata.target = target
        #         extractdata.datadate = reporting_date
        #         extractdata.curvalue = getextractdata(target, reporting_date)
        #         if target.cumulative == "是":
        #             cumulative = getcumulative(target, reporting_date, extractdata.curvalue)
        #             extractdata.cumulativemonth = cumulative["cumulativemonth"]
        #             extractdata.cumulativequarter = cumulative["cumulativequarter"]
        #             extractdata.cumulativehalfyear = cumulative["cumulativehalfyear"]
        #             extractdata.cumulativeyear = cumulative["cumulativeyear"]
        #         extractdata.save()
        process_id = int(process_id)

        # 实际
        try:
            update_pm = ProcessMonitor.objects.get(id=process_id)
        except ProcessMonitor.DoesNotExist as e:
            logger.info('run_process() >> %s' % e)
        else:
            update_pm.create_time = datetime.datetime.now()
            update_pm.p_id = pid
            update_pm.save()

            app_id = update_pm.app_admin_id
            source_id = update_pm.source_id
            circle_id = update_pm.cycle_id
            extract = Extract(app_id, source_id, circle_id)
            extract.run()
    else:
        logger.info('run_process() >> %s' % '传入参数有误。')


# extract = Extract(1, 2, 2)
# target = Target.objects.get(id=9)
# time = datetime.datetime.now()
# extract.get_row_data(target, time)

# run_process(9, None, None)
if len(sys.argv) > 1:
    run_process(sys.argv[1], None, None)
    logger.info('进程启动。')
    # while True:
    #     # if datetime.datetime.now().minute==10:
    #     #     connection = pymysql.connect(host='192.168.100.154',
    #     #                                  user='root',
    #     #                                  password='password',
    #     #                                  db='datacenter',
    #     #                                  )
    #     #     cursor = connection.cursor()
    #     #     strsql = "select connection from datacenter_source where id=" + sys.argv[1]
    #     #     cursor.execute(strsql)
    #     #     data = cursor.fetchall()
    #     #     if len(data) > 0:
    #     #         processcon = data[0][0]
    #     #         strsql = "select id,code,cumulative,sourcetable,sourcefields,sourceconditions from datacenter_target where (state<>'9' or state is null) and operationtype='16' and source_id=" + sys.argv[1]
    #     #         cursor.execute(strsql)
    #     #         targets = cursor.fetchall()
    #     #         if targets>0:
    #     #             mytargets = []
    #     #             for target in targets:
    #     #                 mytargets.append({"id":target[0],"code":target[1],"cumulative":target[2],"sourcetable":target[3],"sourcefields":target[4],"sourceconditions":target[5]})
    #     #             run_process(sys.argv[1],processcon,mytargets)
    #     #     connection.close()
    #     run_process(sys.argv[1], None, None)
    #     time.sleep(60)
else:
    logger.info('脚本未传参。')
