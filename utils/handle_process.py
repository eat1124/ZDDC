"""
启动进程
"""
import sys
from datetime import datetime
import pymysql.cursors


def run_process(source_id):
    # 启动进程(exe) *******************待修改

    # 修改进程创建时间
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
                update_sql = """UPDATE datacenter.datacenter_source SET create_time='{0}' WHERE id='{1}'""".format(
                    datetime.now(), source_id)
                cursor.execute(update_sql)
            connection.commit()
        finally:
            connection.close()
    else:
        pass


if len(sys.argv) > 1:
    run_process(sys.argv[1])
else:
    print("未传参")
