"""
启动进程
"""
import sys
import os
import subprocess
import pymysql
from datetime import datetime
import time
import json

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


def run_process(process_id,processcon,targets):
    # subprocess.run(r"D:\Sublime\Sublime Text Build 3200 x64\sublime_text.exe")
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
        connection = pymysql.connect(host='192.168.1.66',
                                     user='root',
                                     password='password',
                                     db='datacenter',
                                     charset='utf8mb4',
                                     cursorclass=pymysql.cursors.DictCursor)
        try:
            with connection.cursor() as cursor:
                update_sql = """UPDATE datacenter.datacenter_processmonitor SET last_time='{0}', p_id='{1}' WHERE id='{2}'""".format(
                    datetime.now(), pid, process_id)
                cursor.execute(update_sql)
            connection.commit()
        finally:
            connection.close()
    else:
        pass


if len(sys.argv) > 1:
    while True:
        # if datetime.now().minute==10:
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


