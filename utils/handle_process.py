"""
启动进程
"""
import sys
import os
import subprocess
import pymysql
from datetime import datetime
import time


def run_process(source_id):
    subprocess.run(r"D:\Sublime\Sublime Text Build 3200 x64\sublime_text.exe")
    # 取数 *****************************************************

    pid = os.getpid()

    if source_id:
        source_id = int(source_id)
        connection = pymysql.connect(host='192.168.100.154',
                                     user='root',
                                     password='password',
                                     db='datacenter',
                                     charset='utf8mb4',
                                     cursorclass=pymysql.cursors.DictCursor)
        try:
            with connection.cursor() as cursor:
                update_sql = """UPDATE datacenter.datacenter_source SET last_time='{0}', p_id='{1}' WHERE id='{2}'""".format(
                    datetime.now(), pid, source_id)
                cursor.execute(update_sql)
            connection.commit()
        finally:
            connection.close()
    else:
        pass


if len(sys.argv) > 1:
    while True:
        run_process(sys.argv[1])
        time.sleep(3600)
else:
    print("未传参")


