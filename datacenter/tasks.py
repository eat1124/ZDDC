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

