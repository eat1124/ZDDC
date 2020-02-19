"""
启动进程
"""
import os
import datetime
import time
import json
import copy
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


class Extract(object):
    """
    先补取，后定时取数
    """
    def __init__(self, app_id, source_id, circle_id):
        self.app_id = app_id
        self.source_id = source_id
        self.circle_id = circle_id
        self.pm = None
        self.msg = ''
        try:
            self.pm = ProcessMonitor.objects.get(app_admin_id=self.app_id, source_id=self.source_id, cycle_id=self.circle_id)
        except ProcessMonitor.DoesNotExist as e:
            self.msg = 'ProcessMonitor对象不存在。'

    def supplement(self):
        # 补取
        if self.pm:
            start_time = self.pm.last_time
            end_time = datetime.datetime.now()

            # start_time加上一分钟，低于end_time继续循环补取，超过则停止
            while True:
                one_minute_plus = start_time + datetime.timedelta(minutes=1)
                # 取数
                self.get_data(one_minute_plus)
                if one_minute_plus > end_time:
                    break

            # 补取过程也消耗时间，再次判断进行补取:先把秒数抹掉再比较(啥意思？)
            aft_last_time = self.pm.last_time
            try:
                delta_time = (datetime.datetime.now() - aft_last_time).total_seconds()
            except:
                pass
            else:
                if delta_time > 60:
                    self.supplement()

    def set_timer(self):
        # 定时器
        time_now = datetime.datetime.now()
        self.get_data(time_now)

    def get_data(self, now_time):
        # 取数
        # 判断当前时间是否符合周期规则
        if self.pm:
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
                if storage.storagetag == '行':
                    self.get_row_data(now_time)
                elif storage.storagetag == '列':
                    col_ordered_target = copy_ordered_targets.filter(storage=storage, storagetag=storage.storagetag)

                    self.get_col_data(now_time)
                    # 剔除
                    copy_ordered_targets = copy_ordered_targets.exclude(storage=storage, storagetag=storage.storagetag)
                else:
                    pass


    def get_row_data(self, time):
        # 获取行数据
        pass

    def get_col_data(self, time):
        # 获取列数据
        pass

    def run(self):
        # 补取()
	    # 启动定时器，每分钟执行一次
        self.supplement()
        self.set_timer()


def run_process(process_id, processcon, targets):
    # 取数 *****************************************************
    # SQL Server
    # connection = pymssql.connect(host='127.0.0.1', user='miaokela', password='Passw0rD', database='mkl')
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

        # 判断进程类型 动态还是固定(数据补取：1，数据清理：2，数据服务：3，短信服务：4)

        # if process_info:
        #     # 根据app_id/source_id/circle_id来过滤所有指标来取数
        #     extract = Extract(app_id, source_id, circle_id)
        #     extract.run()
        #     pass

        # 更新数据库状态
        try:
            update_pm = ProcessMonitor.objects.get(id=process_id)
            print(update_pm)
        except ProcessMonitor.DoesNotExist as e:
            print(e)
        else:
            update_pm.last_time = datetime.datetime.now()
            update_pm.p_id = pid
            update_pm.save()
    else:
        pass

# run_process(10, None, None)
if len(sys.argv) > 1:
    while True:
        # if datetime.datetime.now().minute==10:
        #     connection = pymysql.connect(host='192.168.100.154',
        #                                  user='root',
        #                                  password='password',
        #                                  db='datacenter',
        #                                  )
        #     cursor = connection.cursor()
        #     strsql = "select connection from datacenter_source where id=" + sys.argv[1]
        #     cursor.execute(strsql)
        #     data = cursor.fetchall()
        #     if len(data) > 0:
        #         processcon = data[0][0]
        #         strsql = "select id,code,cumulative,sourcetable,sourcefields,sourceconditions from datacenter_target where (state<>'9' or state is null) and operationtype='16' and source_id=" + sys.argv[1]
        #         cursor.execute(strsql)
        #         targets = cursor.fetchall()
        #         if targets>0:
        #             mytargets = []
        #             for target in targets:
        #                 mytargets.append({"id":target[0],"code":target[1],"cumulative":target[2],"sourcetable":target[3],"sourcefields":target[4],"sourceconditions":target[5]})
        #             run_process(sys.argv[1],processcon,mytargets)
        #     connection.close()
        run_process(sys.argv[1], None, None)
        time.sleep(60)
else:
    print("未传参")
