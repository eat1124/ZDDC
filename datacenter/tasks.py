from __future__ import absolute_import
from celery import shared_task
import pymssql
from datacenter.models import *
from django.db import connection
from xml.dom.minidom import parse, parseString
from . import remote
from .models import *
from .funcs import *
import datetime
from django.db.models import Q
import time
import subprocess
import psutil
from ZDDC.settings import BASE_DIR
import os


@shared_task
def handle_process(source_id, handle_type=None):
    """
    开启程序
    """
    current_process = Source.objects.filter(id=source_id)
    if current_process.exists():
        current_process = current_process[0]

        if handle_type == "RUN":
            try:
                # 修改数据库进程状态
                current_process.status = "开启中"
                current_process.create_time = datetime.datetime.now()
                current_process.save()
                process_path = BASE_DIR + os.sep + "utils" + os.sep + "handle_process.py" + " {0}".format(source_id)
                os.system(r"{0}".format(process_path))
            except Exception as e:
                print("执行失败，原因：", e)

        elif handle_type == "DESTROY":
            pid = current_process.p_id
            if pid:
                all_process = psutil.process_iter()
                for p in all_process:
                    if int(pid) == p.pid:
                        try:
                            p.terminate()

                            # 修改数据库进程状态
                            current_process.status = "已关闭"
                            current_process.create_time = None
                            current_process.p_id = ""
                            current_process.save()
                        except:
                            print("程序终止失败。")
            else:
                print("该进程不存在。")
        else:
            print("程序执行类型不符合。")
    else:
        print("数据源不存在。")


@shared_task
def monitor_process():
    """
    监控程序
        1.处理进程异常关闭提示。
    """
    all_term_process = psutil.process_iter()
    process_info_list = []
    for p in all_term_process:
        try:
            process_info_list.append({
                "id": p.pid,
                "status": p.status(),
                "create_time": p.create_time(),
            })
        except:
            pass
    p_source = Source.objects.filter(pnode=None).exclude(state="9")
    if p_source.exists():
        p_source = p_source[0]

        all_db_process = Source.objects.exclude(state="9").filter(pnode=p_source)
        if all_db_process.exists():
            for db_process in all_db_process:
                error_running = True
                db_process_id = db_process.p_id
                if db_process_id:
                    for term_process in process_info_list:
                        if int(db_process_id) == term_process["id"]:
                            error_running = False
                            try:
                                db_process.status = term_process["status"]
                                db_process.create_time = datetime.datetime.fromtimestamp(term_process["create_time"])
                                db_process.save()
                                break
                            except Exception as e:
                                print("保存失败，原因", e)

                if error_running and db_process.status == "running":
                    try:
                        db_process.status = "进程异常关闭，请重新启动。"
                        db_process.save()
                        break
                    except Exception as e:
                        print("保存失败，原因", e)
    else:
        pass

