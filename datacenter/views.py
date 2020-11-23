# coding:utf-8
import time
import datetime
import sys
import os
import json
import random
import uuid
import xml.dom.minidom
from xml.dom.minidom import parse, parseString
import xlrd
import xlwt
import pymssql
from lxml import etree
import re
import pdfkit
import sys
import requests
from operator import itemgetter
import subprocess
import multiprocessing
import decimal
import pymysql
import psutil
import base64
import win32api
import calendar
import socket
from dateutil.relativedelta import relativedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.utils.timezone import utc
from django.utils.timezone import localtime
from django.shortcuts import render
from django.contrib import auth
from django.template import RequestContext
from django.http import HttpResponseRedirect, Http404, HttpResponse, JsonResponse, FileResponse
from django.http import StreamingHttpResponse
from django.db.models import Q
from django.db.models import Count
from django.db.models import Sum, Max, Avg, Min
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from django.utils.encoding import escape_uri_path
from django.core.mail import send_mail
from django.forms.models import model_to_dict
from django.template.response import TemplateResponse
from django.views.generic import View
from django.db import transaction

from datacenter.tasks import *
from .models import *
from .remote import ServerByPara
from ZDDC import settings
from .funcs import *
from .ftp_file_handler import *
from utils.handle_process import Extract, PIQuery, get_dict_name

funlist = []

info = {"webaddr": "cv-server", "port": "81", "username": "admin", "passwd": "Admin@2017", "token": "",
        "lastlogin": 0}


def report_server(request, funid):
    if request.user.is_authenticated():
        rs = ReportServer.objects.first()
        id, report_server, user_name, password, report_file_path, web_server, ps_script_path = 0, '', '', '', '', '', ''
        if rs:
            id = rs.id
            report_server = rs.report_server
            user_name = rs.username
            password = rs.password
            report_file_path = rs.report_file_path
            web_server = rs.web_server
            ps_script_path = rs.ps_script_path

        return render(request, 'report_server.html',
                      {'username': request.user.userinfo.fullname, "pagefuns": getpagefuns(funid),
                       'id': id, 'report_server': report_server, 'user_name': user_name,
                       'password': password, 'report_file_path': report_file_path,
                       'web_server': web_server, 'ps_script_path': ps_script_path
                       })
    else:
        return HttpResponseRedirect('/login')


def report_server_save(request):
    if request.user.is_authenticated():
        id = request.POST.get('id', '')
        report_server = request.POST.get('report_server', '')
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        report_file_path = request.POST.get('report_file_path', '')

        status = 0
        data = ''

        try:
            id = int(id)
        except:
            status = 0
            data = '网络连接异常。'
        else:
            if id == 0:
                rs = ReportServer()
                rs.report_server = report_server
                rs.username = username
                rs.password = password
                rs.report_file_path = report_file_path
                rs.save()
                status = 1
                data = '保存成功。'
            else:
                try:
                    rs = ReportServer.objects.get(id=id)
                except ReportServer.DoesNotExist as e:
                    status = 0
                    data = '报表记录不存在。'
                else:
                    rs.report_server = report_server
                    rs.username = username
                    rs.password = password
                    rs.report_file_path = report_file_path
                    rs.save()
                    status = 1
                    data = '保存成功。'
        return JsonResponse({
            'status': status,
            'data': data
        })
    else:
        return HttpResponseRedirect('/login')


def Digit(digit):
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


class DataCenter(View):
    """
    数据服务
    """

    def get(self, request):
        # 2020-02-20
        result = {}
        target_name = request.GET.get('target_name', '')
        date = request.GET.get('date', '')

        if not target_name:
            return JsonResponse({
                'status': 0,
                'data': {},
                'msg': '指标名称未传入。'
            })

        try:
            date = datetime.datetime.strptime(date, '%Y-%m-%d')

            # >=当天0时 <昨日0时
            end_time = date + datetime.timedelta(days=1)
        except:
            return JsonResponse({
                'status': 0,
                'data': {},
                'msg': '传入时间有误。'
            })
        extract_data = getmodels('Extractdata', str(date.year)).objects.exclude(state='9').filter(datadate__gte=date,
                                                                                                  datadate__lt=end_time,
                                                                                                  target__name=target_name)
        data_list = []
        for ed in extract_data:
            data_list.append({
                'target_name': ed.target.name,
                'datadate': ed.datadate,
                'curvalue': ed.curvalue,
                'curvaluedate': ed.curvaluedate,
                'curvaluetext': ed.curvaluetext,
                'cumulativemonth': ed.cumulativemonth,
                'cumulativequarter': ed.cumulativequarter,
                'cumulativehalfyear': ed.cumulativehalfyear,
                'cumulativeyear': ed.cumulativeyear,
            })
        result['status'] = 1
        result['data'] = data_list
        result['msg'] = '获取数据成功。'

        return JsonResponse(result, json_dumps_params={'ensure_ascii': False})


def getmodels(modelname, year):
    try:
        from django.apps import apps

        mydata = apps.get_model('__main__', modelname + '_' + year)
    except LookupError:
        if modelname == "Meterdata":
            mydata = get_meterdata_model(year)
        elif modelname == "entrydata":
            mydata = get_entrydata_model(year)
        elif modelname == "Extractdata":
            mydata = get_extractdata_model(year)
        elif modelname == "Calculatedata":
            mydata = get_calculatedata_model(year)
        else:
            mydata = get_entrydata_model(year)

    if not mydata.is_exists():
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(mydata)
    return mydata


def get_process_monitor_tree(request):
    if request.user.is_authenticated():
        cycle_id = request.POST.get('cycle_id', '')
        app_id = request.POST.get('app_id', '')
        source_id = request.POST.get('source_id', '')
        index = request.POST.get('index', '')
        try:
            cycle_id = int(cycle_id)
            app_id = int(app_id)
            source_id = int(source_id)
        except ValueError as e:
            print(e)
        targets = Target.objects.filter(operationtype__in=[16, 1]).exclude(state=9).values('source_id', 'adminapp_id',
                                                                                           'cycle_id')

        def does_it_exist(source, adminapp=None, cycle=None):
            if source and not any([adminapp, cycle]):
                for t in targets:
                    if source == t['source_id']:
                        return True
            if all([source, adminapp]) and not cycle:
                for t in targets:
                    if source == t['source_id'] and adminapp == t['adminapp_id']:
                        return True
            if all([source, adminapp, cycle]):
                for t in targets:
                    if source == t['source_id'] and adminapp == t['adminapp_id'] and cycle == t['cycle_id']:
                        return True
            return False

        # 进程监控 >> 数据源配置 >> (指标管理中匹配)应用>> (指标管理中心根据数据源+应用匹配)周期
        # 根节点
        root_info = dict()
        root_info['text'] = "进程监控"
        root_info['type'] = 'node'

        # 1.数据源管理
        source = Source.objects.exclude(state='9')
        app = App.objects.exclude(state='9')
        cycle = Cycle.objects.exclude(state='9')

        variable_info_list = []
        fixed_info_list = []
        for s in source:
            # 指标管理中匹配
            if not s.type:
                if does_it_exist(s.id):
                    # 数据源类型
                    source_type = ""
                    try:
                        source_type = DictList.objects.get(id=s.sourcetype).name
                    except DictList.DoesNotExist as e:
                        print(e)

                    s_info = dict()
                    s_info['text'] = s.name
                    s_info['type'] = 'node'
                    s_info['data'] = {
                        's_id': s.id,
                        's_name': s.name,
                        's_code': s.code,
                        's_type': source_type,
                        'type': 'source'
                    }
                    s_info['state'] = {'opened': True}

                    # 2.应用
                    a_info_list = []
                    for a in app:
                        if does_it_exist(s.id, a.id):
                            a_info = dict()
                            a_info['text'] = a.name
                            a_info['type'] = 'node'
                            a_info['data'] = {
                                's_id': s.id,
                                's_name': s.name,
                                's_code': s.code,
                                's_type': source_type,
                                'a_id': a.id,
                                'a_name': a.name,
                                'type': 'app'
                            }
                            a_info['state'] = {'opened': True}

                            # 3.周期
                            c_info_list = []

                            for c in cycle:
                                if does_it_exist(s.id, a.id, c.id):
                                    create_time, last_time, status = '', '', ''
                                    cp_id = ''
                                    # 获取进程状态
                                    cps = ProcessMonitor.objects.filter(source_id=s.id).filter(
                                        app_admin_id=a.id).filter(
                                        cycle_id=c.id).exclude(state='9')
                                    if cps.exists():
                                        cp = cps[0]
                                        cp_id = cp.id
                                        create_time = '{:%Y-%m-%d %H:%M:%S}'.format(
                                            cp.create_time) if cp.create_time else ""
                                        last_time = '{:%Y-%m-%d %H:%M:%S}'.format(cp.last_time) if cp.last_time else ""
                                        status = cp.status
                                        if index == "0":
                                            # 更新数据库数据：进程状态
                                            p_id = int(cp.p_id) if cp.p_id else ""
                                            if p_id:
                                                py_process = check_py_exists(p_id)
                                                if not py_process:
                                                    cp.status = "已关闭"
                                                    cp.save()
                                                    status = "已关闭"

                                    c_info = dict()
                                    c_info['text'] = c.name
                                    c_info['type'] = 'file'
                                    c_info['data'] = {
                                        's_id': s.id,
                                        's_name': s.name,
                                        's_code': s.code,
                                        's_type': source_type,
                                        'a_name': a.name,
                                        'a_id': a.id,
                                        'c_id': c.id,
                                        'c_name': c.name,
                                        'type': 'cycle',

                                        # 主进程id
                                        'cp_id': cp_id,

                                        # 进程状态
                                        'create_time': create_time,
                                        'last_time': last_time,
                                        'status': status
                                    }

                                    c_info['state'] = {'opened': True}
                                    #
                                    if cycle_id == c.id and app_id == a.id and source_id == s.id:
                                        c_info['state']['selected'] = True

                                    # 判断进程状态
                                    if status != "运行中":
                                        c_info['type'] = 'file_grey'
                                        a_info['type'] = 'node_grey'
                                        s_info['type'] = 'node_grey'
                                        root_info['type'] = 'node_grey'
                                    c_info_list.append(c_info)
                            a_info['children'] = c_info_list

                            a_info_list.append(a_info)
                    s_info['children'] = a_info_list

                    variable_info_list.append(s_info)
            else:
                # 固定节点(数据补取、数据清理、数据服务、短信服务)
                fixed_s_info = dict()
                fixed_s_info['text'] = s.name
                fixed_s_info['type'] = 'file'

                # 进程状态
                f_create_time, f_last_time, f_status = '', '', ''
                # 获取进程状态
                f_cps = ProcessMonitor.objects.filter(source_id=s.id).exclude(state='9')
                if f_cps.exists():
                    f_cp = f_cps[0]
                    f_create_time = '{:%Y-%m-%d %H:%M:%S}'.format(
                        f_cp.create_time) if f_cp.create_time else ""
                    f_last_time = '{:%Y-%m-%d %H:%M:%S}'.format(f_cp.last_time) if f_cp.last_time else ""
                    f_status = f_cp.status
                    if index == "0":
                        # 更新数据库数据：进程状态
                        p_id = int(f_cp.p_id) if f_cp.p_id else ""
                        if p_id:
                            py_process = check_py_exists(p_id)
                            if not py_process:
                                f_cp.status = "已关闭"
                                f_cp.save()
                                f_status = "已关闭"

                # 判断进程状态
                if f_status != "运行中":
                    fixed_s_info['type'] = 'file_grey'
                    root_info['type'] = 'node_grey'

                fixed_s_info['data'] = {
                    'check_type': s.type,

                    'f_s_name': s.name,
                    's_id': s.id,
                    # 进程状态
                    'create_time': f_create_time,
                    'last_time': f_last_time,
                    'status': f_status
                }
                fixed_info_list.append(fixed_s_info)

        # 固定进程放在后面
        variable_info_list.extend(fixed_info_list)
        root_info['children'] = variable_info_list
        root_info['state'] = {'opened': True}
        root_info['data'] = {
            'type': 'root'
        }

        tree_data = json.dumps([root_info], ensure_ascii=False)
        return JsonResponse({
            "ret": 1,
            "data": tree_data
        })
    else:
        return HttpResponseRedirect("/login")


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


def process_monitor_index(request, funid):
    """
    进程监控
    """
    if request.user.is_authenticated():
        # 检测进程是否启动
        process_monitors = ProcessMonitor.objects.exclude(state='9')

        shutdown_process_set = set()
        for process_monitor in process_monitors:
            p_id = process_monitor.p_id
            try:
                p_id = int(p_id)
            except ValueError as e:
                shutdown_process_set.add(process_monitor.id)
            else:
                py_process = check_py_exists(p_id)
                if not py_process:
                    shutdown_process_set.add(process_monitor.id)
        if shutdown_process_set:
            process_monitors.filter(id__in=shutdown_process_set).update(**{
                'status': '已关闭', 'create_time': None, 'p_id': ''
            })
        return render(request, 'process_monitor.html',
                      {'username': request.user.userinfo.fullname,
                       "pagefuns": getpagefuns(funid)})
    else:
        return HttpResponseRedirect("/login")


def process_monitor_data(request):
    if request.user.is_authenticated():
        result = []
        p_source = Source.objects.filter(pnode=None).exclude(state="9").filter(type='')
        if p_source.exists():
            p_source = p_source[0]
        else:
            return JsonResponse({"data": []})
        all_source = Source.objects.exclude(state="9").filter(pnode=p_source).filter(type='')
        for source in all_source:
            source_type = source.sourcetype
            if source_type:
                source_type = int(source_type)
                try:
                    temp_dict_list = DictList.objects.exclude(state="9").get(id=source_type)
                    source_type_list = get_select_source_type(temp_source_type=source_type)

                    result.append({
                        "id": source.id,
                        "name": source.name,
                        "code": source.code,
                        "sourcetype": source_type,
                        "sourcetype_name": temp_dict_list.name,
                        "source_type_list": source_type_list,
                        "create_time": source.create_time.strftime(
                            '%Y-%m-%d %H:%M:%S') if source.create_time else "未启动",
                        "last_time": source.last_time.strftime(
                            '%Y-%m-%d %H:%M:%S') if source.last_time else "未启动",
                        "status": source.status if source.status else "",
                    })
                except Exception as e:
                    print(e)

        return JsonResponse({"data": result})


def handle_process(current_process, handle_type=None):
    """
    操作程序
        已关闭
        运行中
    """
    tag, res = "", ""

    if handle_type == "RUN":
        try:
            process_path = BASE_DIR + os.sep + "utils" + os.sep + "handle_process.py" + " {0}".format(
                current_process.id)

            # 启动前，清理当前未关闭的进程,避免同ID的进程在取数
            python_process = [p for p in psutil.process_iter() if 'python' in p.name()]

            for pp in python_process:
                try:
                    # ['C:\\Python35\\python.exe', '-i', 'D:\\Pros\\ZDDC\\utils\\handle_process.py', '14']
                    if 'handle_process.py' in pp.as_dict()['cmdline'][2] and current_process.id == int(
                            pp.as_dict()['cmdline'][3]):
                        pp.terminate()
                except:
                    pass

            win32api.ShellExecute(0, 'open', 'python', r'-i {process_path}'.format(process_path=process_path), '', 0)
            res = "程序启动成功。"
            tag = 1
        except Exception as e:
            print(e)
            res = "程序启动失败"
        if tag == 1:
            # 修改数据库进程状态
            current_process.status = "运行中"
            current_process.create_time = datetime.datetime.now()
            current_process.save()
    elif handle_type == "DESTROY":
        pid = current_process.p_id
        if pid:
            py_process = check_py_exists(pid)
            if py_process:
                py_process.terminate()

                # 修改数据库进程状态
                current_process.status = "已关闭"
                current_process.create_time = None
                current_process.p_id = ""
                current_process.save()
                res = "程序终止成功。"
                tag = 1
            else:
                res = "未找到该进程"
        else:
            res = "该进程不存在。"
    else:
        res = "程序执行类型不符合。"

    return (tag, res)


def process_run(request):
    if request.user.is_authenticated():
        tag, res = 0, ""

        source_id = request.POST.get("source_id", "")
        app_id = request.POST.get("app_id", "")
        cycle_id = request.POST.get("cycle_id", "")
        operate = request.POST.get("operate", "")
        check_type = request.POST.get("check_type", "")
        try:
            source_id = int(source_id)
            app_id = int(app_id)
            cycle_id = int(cycle_id)
        except ValueError as e:
            print(e)

        # 进程操作记入日志
        def record_log(app_id, source_id, cycle_id, msg):
            try:
                log = LogInfo()
                log.source_id = source_id
                log.app_id = app_id
                log.cycle_id = cycle_id
                log.create_time = datetime.datetime.now()
                log.content = msg
                log.save()
            except:
                pass

        # 固定进程
        current_process = ProcessMonitor.objects.filter(source_id=source_id).exclude(state='9')

        # 动态进程
        if not check_type:
            current_process = ProcessMonitor.objects.filter(source_id=source_id).filter(app_admin_id=app_id).filter(
                cycle_id=cycle_id).exclude(state='9')

        if current_process.exists():
            current_process = current_process[0]

            def get_running_info(current_process):
                # 获取运行状态与启动时间
                status = current_process.status
                create_time = current_process.create_time
                return {
                    'status': status,
                    'create_time': '{:%Y-%m-%d %H:%M:%S}'.format(create_time) if create_time else ''
                }

            if operate == 'start':
                # 查看是否运行中
                if current_process.status == "运行中":
                    tag = 0
                    res = "请勿重复执行该程序。"
                else:
                    tag, res = handle_process(current_process, handle_type="RUN")
                    record_log(app_id, source_id, cycle_id, '进程启动成功。')
            elif operate == 'stop':
                if current_process.status != "运行中":
                    tag = 0
                    res = "当前进程未在运行中。"
                else:
                    tag, res = handle_process(current_process, handle_type="DESTROY")
                    record_log(app_id, source_id, cycle_id, '进程关闭成功。')
            elif operate == 'restart':
                if current_process.status != "运行中":
                    tag = 0
                    res = "当前进程未在运行中，请启动程序。"
                else:
                    tag, res = handle_process(current_process, handle_type="DESTROY")
                    if tag == 1:
                        tag, res = handle_process(current_process, handle_type="RUN")
                        record_log(app_id, source_id, cycle_id, '进程重启成功。')
                    else:
                        tag = 0
                        res = "关闭进程失败。"
            else:
                tag = 0
                res = "未接收到操作指令。"
            return JsonResponse({
                'tag': tag,
                'res': res,
                'data': get_running_info(current_process)
            })
        else:
            current_process = ProcessMonitor()
            current_process.source_id = source_id
            if not check_type:
                current_process.app_admin_id = app_id
                current_process.cycle_id = cycle_id
            current_process.save()
            tag, res = handle_process(current_process, handle_type="RUN")
            record_log(app_id, source_id, cycle_id, '进程启动成功。')
            return JsonResponse({
                'tag': tag,
                'res': res,
                'data': ''
            })


def pm_target_data(request):
    """
    根据应用、数据源、周期 过滤出所有指标
    :param request:
    :return:
    """
    if request.user.is_authenticated():
        app_id = request.GET.get('app_id', '')
        source_id = request.GET.get('source_id', '')
        cycle_id = request.GET.get('cycle_id', '')

        result = []

        supplement_status = '0'  # 1启动成功 0完成 2失败
        try:
            app_id = int(app_id)
            source_id = int(source_id)
            cycle_id = int(cycle_id)
        except ValueError as e:
            print(e)
        else:
            targets = Target.objects.exclude(state='9').filter(
                Q(adminapp_id=app_id) & Q(source_id=source_id) & Q(cycle_id=cycle_id)).select_related('storage')

            for target in targets:
                result.append({
                    'id': target.id,
                    'target_code': target.code,
                    'target_name': target.name,
                    'source_content': target.source_content,
                    'storage_table_name': target.storage.tablename if target.storage else '',
                    'storage_fields': target.storagefields[:-1] if target.storagefields.endswith(
                        ',') else target.storagefields
                })

            # 补取进程的状态 1/0/2
            try:
                primary_process = ProcessMonitor.objects.exclude(state='9').get(app_admin_id=app_id,
                                                                                source_id=source_id,
                                                                                cycle_id=cycle_id)
            except ProcessMonitor.DoesNotExist as e:
                print(e)
            else:
                supplement_process = SupplementProcess.objects.exclude(state='9').filter(
                    primary_process=primary_process).last()
                supplement_status = supplement_process.p_state if supplement_process else '0'

        return JsonResponse({
            "data": result,
            'supplement_status': supplement_status
        })
    else:
        return HttpResponseRedirect("/login")


def get_exception_data(request):
    if request.user.is_authenticated():
        result = []
        app_id = request.GET.get('app_id', '')
        source_id = request.GET.get('source_id', '')
        cycle_id = request.GET.get('cycle_id', '')

        try:
            app_id = int(app_id)
            source_id = int(source_id)
            cycle_id = int(cycle_id)
        except ValueError as e:
            print(e)
        else:
            t_now = datetime.datetime.now()

            t_before = t_now - datetime.timedelta(days=90)
            t_after = t_now + datetime.timedelta(days=90)

            exceptions = ExceptionData.objects.filter(
                app_id=app_id, source_id=source_id, cycle_id=cycle_id
            ).filter(extract_error_time__range=[t_before, t_after]).exclude(state=9).order_by('-id')
            for exception in exceptions:
                result.append({
                    'id': exception.id,
                    'target_name': exception.target.name if exception.target else '',
                    'extract_error_time': '{:%Y-%m-%d %H:%M:%S}'.format(
                        exception.extract_error_time) if exception.extract_error_time else '',
                    'supplement_times': exception.supplement_times,
                    'last_supplement_time': '{:%Y-%m-%d %H:%M:%S}'.format(
                        exception.last_supplement_time) if exception.last_supplement_time else '',
                })
        return JsonResponse({"data": result})
    else:
        return HttpResponseRedirect("/login")


def exception_data_del(request):
    if request.user.is_authenticated():
        status = 1
        data = ''
        id = request.POST.get('id', '')
        try:
            id = int(id)
            ex_data = ExceptionData.objects.get(id=id)
        except:
            status = 0
            data = '该异常信息不存在。'
        else:
            ex_data.state = "9"
            ex_data.save()
            status = 1
            data = '删除成功。'

        return JsonResponse({
            'status': status,
            'data': data
        })


def get_log_info(request):
    if request.user.is_authenticated():
        result = []
        app_id = request.GET.get('app_id', '')
        source_id = request.GET.get('source_id', '')
        cycle_id = request.GET.get('cycle_id', '')

        try:
            app_id = int(app_id)
            source_id = int(source_id)
            cycle_id = int(cycle_id)
        except ValueError as e:
            print(e)
        else:
            t_now = datetime.datetime.now()

            t_before = t_now - datetime.timedelta(days=90)
            t_after = t_now + datetime.timedelta(days=90)

            log_infos = LogInfo.objects.filter(
                Q(app_id=app_id) & Q(source_id=source_id) & Q(cycle_id=cycle_id)
            ).filter(create_time__range=[t_before, t_after]).order_by('-create_time')

            for num, log_info in enumerate(log_infos):
                result.append({
                    'id': num + 1,
                    'create_time': '{:%Y-%m-%d %H:%M:%S}'.format(
                        log_info.create_time) if log_info.create_time else '',
                    'content': log_info.content,
                })
        return JsonResponse({"data": result})
    else:
        return HttpResponseRedirect("/login")


def target_test(request):
    """
    选择数据源测试取数
    :param request:
    :return:
    """
    if request.user.is_authenticated():
        selectedtarget = request.POST.get('selectedtarget', '[]')
        result = {
            "status": 1,
            "data": [],
        }

        class DecimalEncoder(json.JSONEncoder):
            """
            解决Decimal无法序列化问题
            """

            def default(self, obj):
                if isinstance(obj, decimal.Decimal):
                    return float(obj)
                return super(DecimalEncoder, self).default(obj)

        try:
            now_time = datetime.datetime.now()

            targets = Target.objects.filter(id__in=eval(selectedtarget))
            tmp_list = []
            for target in targets:
                ret = Extract.getDataFromSource(target, now_time)
                result_list = ret['result']
                error = ret['error']

                if error:
                    tmp_list.append({
                        "target_id": target.id,
                        "target_code": target.code,
                        "target_name": target.name,
                        "data": error,
                        "status": 'ERROR'
                    })
                else:
                    tmp_list.append({
                        "target_id": target.id,
                        "target_code": target.code,
                        "target_name": target.name,
                        "data": result_list,
                        "status": 'SUCCESS'
                    })
        except Exception as e:
            print(e)
            result['status'] = 0
        else:
            result['data'] = json.dumps(tmp_list, cls=DecimalEncoder)

        """
        [{
            "target_id": "",
            "target_code": "",
            "target_name": "",
            "data": [...],
            "status": "SUCCESS"
        }, {
            "target_id": "",
            "target_code": "",
            "target_name": "",
            "data": "",
            "status": "ERROR"
        }]

        """
        return JsonResponse(result)
    else:
        return HttpResponseRedirect("/login")


def supplement_process(request):
    """
    选择数据源指定区间补取数据
    :param request:
    :return:
    """
    if request.user.is_authenticated():
        result = {
            'status': 1,
            'data': '成功启动补取。'
        }

        selectedtarget = request.POST.get('selectedtarget', '[]')
        start_time = request.POST.get('start_time', '')
        end_time = request.POST.get('end_time', '')
        cp_id = request.POST.get('cp_id', '')

        try:
            selectedtarget = eval(selectedtarget)
        except:
            pass

        try:
            cp_id = int(cp_id)
        except:
            result['status'] = 0
            result['data'] = '启动补取失败。'
        else:
            if not start_time:
                result['status'] = 0
                result['data'] = '开始时间未填写。'
            elif not end_time:
                result['status'] = 0
                result['data'] = '结束时间未填写。'
            else:
                # 先存入数据库
                try:
                    start_time = datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
                except Exception as e:
                    print(e)
                    start_time = None
                try:
                    end_time = datetime.datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
                except Exception as e:
                    print(e)
                    end_time = None
                if all([start_time, end_time]):
                    if start_time > end_time:
                        return JsonResponse({
                            'status': 0,
                            'data': '开始时间不得迟于结束时间。'
                        })

                supplement_process = SupplementProcess()
                supplement_process.start_time = start_time
                supplement_process.end_time = end_time
                supplement_process.p_state = '1'
                supplement_process.primary_process_id = cp_id
                supplement_process.setup_time = datetime.datetime.now()
                supplement_process.save()

                tmp_selectedtarget = ''

                if type(selectedtarget) == tuple:
                    for st in selectedtarget:
                        tmp_selectedtarget += str(st) + '^'
                else:
                    tmp_selectedtarget = str(selectedtarget)

                process_path = BASE_DIR + os.sep + "utils" + os.sep + "handle_process.py" + " {0} {1}".format(
                    cp_id, tmp_selectedtarget if not tmp_selectedtarget.endswith('^') else tmp_selectedtarget[:-1]
                )

                try:
                    win32api.ShellExecute(0, 'open', 'python', r'-i {process_path}'.format(process_path=process_path),
                                          '', 0)
                except:
                    result['status'] = 0
                    result['data'] = '启动补取失败。'

        return JsonResponse(result)
    else:
        return HttpResponseRedirect("/login")


def get_supplement_process_info(request):
    """
    获取补取进程信息
    :param request:
    :return:
    """
    if request.user.is_authenticated():
        cp_id = request.POST.get('cp_id', '')
        result = {
            'status': 1,
            'data': ''
        }
        try:
            cp_id = int(cp_id)
        except:
            result['status'] = 0
            result['data'] = '获取补取进程信息失败。'
        else:
            sp = SupplementProcess.objects.exclude(state='9').filter(primary_process_id=cp_id).last()
            if sp:
                p_id = sp.p_id
                setup_time = sp.setup_time
                update_time = sp.update_time
                p_state = sp.p_state
                start_time = sp.start_time
                end_time = sp.end_time
                progress_time = sp.progress_time
                result['data'] = {
                    'p_id': p_id,
                    'setup_time': '{:%Y-%m-%d %H:%M:%S}'.format(setup_time) if setup_time else '',
                    'update_time': '{:%Y-%m-%d %H:%M:%S}'.format(update_time) if update_time else '',
                    'p_state': p_state,
                    'start_time': '{:%Y-%m-%d %H:%M:%S}'.format(start_time) if start_time else '',
                    'end_time': '{:%Y-%m-%d %H:%M:%S}'.format(end_time) if end_time else '',
                    'progress_time': '{:%Y-%m-%d %H:%M:%S}'.format(progress_time) if progress_time else '',
                }
            else:
                result['status'] = 0
                result['data'] = '补取进程不存在。'

        return JsonResponse(result)
    else:
        return HttpResponseRedirect("/login")


def get_process_monitor_info(request):
    """
    获取取数进程信息
    :param request:
    :return:
    """
    if request.user.is_authenticated():
        cp_id = request.POST.get('cp_id', '')
        result = {
            'status': 1,
            'data': ''
        }
        try:
            cp_id = int(cp_id)
        except:
            result['status'] = 0
            result['data'] = '获取补取进程信息失败。'
        else:
            try:
                pm = ProcessMonitor.objects.get(id=cp_id)
            except ProcessMonitor.DoesNotExist as e:
                result['status'] = 0
                result['data'] = '取数进程不存在。'
            else:
                source_name = pm.source.name if pm.source else ''
                source_code = pm.source.code if pm.source else ''
                # 数据源类型
                source_type = ""
                try:
                    source_type = DictList.objects.get(id=pm.source.sourcetype).name
                except Exception as e:
                    print(e)
                app_name = pm.app_admin.name if pm.app_admin else ''
                cycle_name = pm.cycle.name if pm.cycle else ''
                status = pm.status
                create_time = '{:%Y-%m-%d %H:%M:%S}'.format(pm.create_time) if pm.create_time else ''
                last_time = '{:%Y-%m-%d %H:%M:%S}'.format(pm.last_time) if pm.last_time else ''

                result['data'] = {
                    'source_name': source_name,
                    'source_code': source_code,
                    'source_type': source_type,
                    'app_name': app_name,
                    'cycle_name': cycle_name,
                    'create_time': create_time,
                    'last_time': last_time,
                    'status': status,
                }
        return JsonResponse(result)
    else:
        return HttpResponseRedirect("/login")


@csrf_exempt
def download_file(request):
    file_name = request.GET.get("file_name", "")
    try:
        c_file_path = settings.BASE_DIR + os.sep + "datacenter" + os.sep + "upload" + os.sep + "report_doc" + os.sep + file_name
        file = open(c_file_path, 'rb')
        response = FileResponse(file)
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Disposition'] = 'attachment;filename="{0}"'.format(
            escape_uri_path(file_name))  # escape_uri_path()解决中文名文件
        return response
    except:
        return HttpResponseRedirect("/report")


def report_index(request, funid):
    """
    报表管理
    """
    if request.user.is_authenticated():
        errors = []
        id = ""
        report_type_list = []

        # 下拉框选项
        c_dict_index_1 = DictIndex.objects.filter(
            id=7).exclude(state='9')
        if c_dict_index_1.exists():
            c_dict_index_1 = c_dict_index_1[0]
            dict_list1 = c_dict_index_1.dictlist_set.exclude(state="9")
            for i in dict_list1:
                report_type_list.append({
                    "report_name": i.name,
                    "report_type_id": i.id,
                })
        all_app = App.objects.exclude(state="9")
        all_app_list = []
        for app in all_app:
            all_app_list.append({
                "app_id": app.id,
                "app_name": app.name,
            })

        # 新增/修改报表模型
        if request.method == "POST":
            id = request.POST.get("id", "")
            name = request.POST.get("name", "")
            code = request.POST.get("code", "")
            report_type = request.POST.get("report_type", "")
            app = request.POST.get("app", "")
            sort = request.POST.get("sort", "")
            # 二进制文件数据
            my_file = request.FILES.get("report_file", None)

            file_name = my_file.name if my_file else ""

            # 是否报表模板
            if_template = request.POST.get("if_template", "")
            try:
                if_template = int(if_template)
            except Exception:
                pass

            # 报表信息组(键值对)的数量
            report_info_num = 0
            for key in request.POST.keys():
                if "report_info_" in key:
                    report_info_num += 1

            try:
                id = int(id)
            except:
                raise Http404()

            # 新增时提示导入文件
            if not my_file and id == 0:
                errors.append("请选择要导入的文件。")
            else:
                if if_contains_sign(file_name):
                    errors.append(r"""请注意文件命名格式，'\/"*?<>'符号文件不允许上传。""")
                else:
                    # 报表存储位置
                    myfilepath = settings.BASE_DIR + os.sep + "datacenter" + os.sep + "upload" + os.sep + "report_doc" + os.sep + file_name
                    # 判断数据库中文件存储记录
                    c_exist_model = ReportModel.objects.filter(file_name=file_name).exclude(state="9")

                    # 新增时判断是否存在，修改时覆盖，不需要判断
                    if c_exist_model.exists() and id == 0:
                        errors.append("该文件已存在,请勿重复上传。")
                    else:
                        if name.strip() == '':
                            errors.append('报表名称不能为空。')
                        else:
                            if code.strip() == '':
                                errors.append('报表编码不能为空。')
                            else:
                                if report_type.strip() == '':
                                    errors.append('报表类别不能为空。')
                                else:
                                    if app.strip() == '' and if_template == 0:
                                        errors.append('关联应用不能为空。')
                                    else:
                                        write_tag = False
                                        # 新增 或者 修改(且有my_file存在) 时写入文件
                                        if id == 0 or id != 0 and my_file:
                                            # 判断请求服务器下载文件条件是否满足
                                            # ps_script_path/report_file_path/web_server/report_server/username/password
                                            rs = ReportServer.objects.first()
                                            if not rs:
                                                errors.append('报表服务器参数未配置，报表上传失败。')
                                            elif not rs.report_server:
                                                errors.append('报表服务器地址未配置，报表上传失败。')
                                            elif not rs.username:
                                                errors.append('报表服务器用户名未配置，报表上传失败。')
                                            elif not rs.password:
                                                errors.append('报表服务器密码未配置，报表上传失败。')
                                            elif not rs.report_file_path:
                                                errors.append('报表存放路径未配置，报表上传失败。')
                                            else:
                                                try:
                                                    with open(myfilepath, 'wb+') as f:
                                                        for chunk in my_file.chunks():
                                                            f.write(chunk)
                                                except:
                                                    errors.append('文件上传失败。')
                                                else:
                                                    # 只要有文件写入，就发送请求
                                                    # 远程执行命令，令远程windows发送请求下载文件
                                                    pre_ps_path = os.path.join(rs.report_file_path, 'report_ps')
                                                    ps_script_path = os.path.join(pre_ps_path, 'request.ps1')
                                                    report_file_path = os.path.join(rs.report_file_path, file_name)
                                                    remote_ip = rs.report_server.split(':')[0]
                                                    remote_user = rs.username
                                                    remote_password = rs.password
                                                    remote_platform = "Windows"

                                                    # 判断ps脚本是否存在
                                                    # 若不存在，创建路径，写入文件
                                                    ps_check_cmd = r'if not exist {pre_ps_path} md {pre_ps_path}'.format(
                                                        pre_ps_path=pre_ps_path)
                                                    ps_script = ServerByPara(ps_check_cmd, remote_ip, remote_user,
                                                                             remote_password, remote_platform)
                                                    ps_result = ps_script.run("")

                                                    if ps_result['exec_tag'] == 1:
                                                        errors.append(ps_result['log'])
                                                    else:
                                                        # 写入脚本文件
                                                        ps_upload_cmd = 'echo param($a, $b) > %s &' % ps_script_path + \
                                                                        'echo $Response=Invoke-WebRequest -Uri $b >> %s &' % ps_script_path + \
                                                                        'echo try{ >> %s &' % ps_script_path + \
                                                                        'echo    [System.IO.File]::WriteAllBytes($a, $Response.Content) >> %s &' % ps_script_path + \
                                                                        'echo }catch{ >> %s &' % ps_script_path + \
                                                                        'echo   [System.Console]::WriteLine($_.Exception.Message) >> %s &' % ps_script_path + \
                                                                        'echo } >> %s &' % ps_script_path
                                                        ps_upload = ServerByPara(ps_upload_cmd, remote_ip, remote_user,
                                                                                 remote_password, remote_platform)
                                                        ps_upload_result = ps_upload.run("")

                                                        if ps_upload_result['exec_tag'] == 1:
                                                            errors.append(ps_upload_result['log'])
                                                        else:
                                                            # 判断报表路径是否存在
                                                            # 若不存在，提示不存在，报表上传失败
                                                            # 获取app_code
                                                            app_code = "TMP"
                                                            if if_template:  # 模板
                                                                app_code = "DATACENTER_TEMPLATE"
                                                            else:
                                                                try:
                                                                    cur_app = App.objects.get(id=int(app))
                                                                    app_code = cur_app.code
                                                                except:
                                                                    pass

                                                            aft_report_file_path = os.path.join(rs.report_file_path, str(app_code))
                                                            report_check_cmd = r'if not exist {report_file_path} md {report_file_path}'.format(
                                                                report_file_path=aft_report_file_path)
                                                            rc = ServerByPara(report_check_cmd, remote_ip,
                                                                              remote_user,
                                                                              remote_password, remote_platform)
                                                            rc_result = rc.run("")

                                                            if rc_result['exec_tag'] == 1:
                                                                errors.append(rc_result['log'])
                                                            else:
                                                                # 获取本地IP
                                                                try:
                                                                    web_server = socket.gethostbyname(
                                                                        socket.gethostname())
                                                                except Exception as e:
                                                                    errors.append("获取服务器IP失败：%s" % e)
                                                                else:
                                                                    url_visited = r"http://{web_server}/download_file?file_name={file_name}".format(
                                                                        web_server=web_server, file_name=file_name)
                                                                    remote_cmd = r'powershell.exe -ExecutionPolicy RemoteSigned -file "{0}" "{1}" "{2}"'.format(
                                                                        ps_script_path,
                                                                        os.path.join(aft_report_file_path,
                                                                                     file_name), url_visited)

                                                                    server_obj = ServerByPara(remote_cmd, remote_ip,
                                                                                              remote_user,
                                                                                              remote_password,
                                                                                              remote_platform)
                                                                    result = server_obj.run("")
                                                                    if result["exec_tag"] == 0:
                                                                        write_tag = True
                                                                    else:
                                                                        errors.append(result['log'])

                                        if id != 0 and not my_file:
                                            write_tag = True
                                        # 远程文件下载成功
                                        if write_tag:
                                            # 新增报表模板
                                            if id == 0:
                                                all_report = ReportModel.objects.filter(
                                                    code=code).exclude(state="9")
                                                if all_report.exists():
                                                    errors.append('报表编码:' + code + '已存在。')
                                                else:
                                                    try:
                                                        report_save = ReportModel()
                                                        report_save.name = name
                                                        report_save.code = code
                                                        report_save.report_type = report_type
                                                        report_save.app_id = int(app) if not if_template else None
                                                        report_save.file_name = file_name
                                                        report_save.sort = int(sort) if sort else None
                                                        report_save.if_template = if_template

                                                        report_save.save()

                                                        if if_template == 0:
                                                            # 关联存储报表模板信息
                                                            if report_info_num:
                                                                range_num = int(report_info_num / 3)
                                                                for i in range(0, range_num):
                                                                    report_info = ReportInfo()
                                                                    report_info_name = request.POST.get(
                                                                        "report_info_name_%d" % (i + 1), "")
                                                                    report_info_default_value = request.POST.get(
                                                                        "report_info_value_%d" % (i + 1), "")
                                                                    if report_info_name:
                                                                        report_info.name = report_info_name
                                                                        report_info.default_value = report_info_default_value
                                                                        report_info.report_model = report_save
                                                                        report_info.save()

                                                        id = report_save.id
                                                    except:
                                                        errors.append('数据异常，请联系管理员!')
                                            # 修改报表模板
                                            else:
                                                all_report = ReportModel.objects.filter(code=code).exclude(
                                                    id=id).exclude(state="9")
                                                if all_report.exists():
                                                    errors.append('存储编码:' + code + '已存在。')
                                                else:
                                                    try:
                                                        report_save = ReportModel.objects.get(
                                                            id=id)
                                                        report_save.name = name
                                                        report_save.code = code
                                                        report_save.report_type = report_type
                                                        report_save.app_id = int(app) if not if_template else None
                                                        if my_file:
                                                            report_save.file_name = file_name
                                                        report_save.sort = int(sort) if sort else None
                                                        report_save.if_template = if_template
                                                        report_save.save()

                                                        if if_template == 0:
                                                            # 修改报表信息关联
                                                            # 情况：报表信息组相对数据库中存储树，增加/减少/相同 一样
                                                            if report_info_num:
                                                                range_num = int(report_info_num / 3)
                                                                current_report_info = report_save.reportinfo_set.exclude(
                                                                    state="9")

                                                                update_id_list = []
                                                                for i in range(0, range_num):
                                                                    report_info_name = request.POST.get(
                                                                        "report_info_name_%d" % (i + 1), "")
                                                                    report_info_default_value = request.POST.get(
                                                                        "report_info_value_%d" % (i + 1), "")
                                                                    report_info_id = request.POST.get(
                                                                        "report_info_id_%d" % (i + 1), "")
                                                                    report_info_id = int(
                                                                        report_info_id) if report_info_id else ""

                                                                    if report_info_id:
                                                                        update_id_list.append(report_info_id)
                                                                        report_info = ReportInfo.objects.filter(
                                                                            id=report_info_id)
                                                                        if report_info.exists() and report_info_name:
                                                                            report_info = report_info[0]
                                                                            report_info.name = report_info_name
                                                                            report_info.default_value = report_info_default_value
                                                                            report_info.report_model = report_save
                                                                            report_info.save()
                                                                    else:
                                                                        report_info = ReportInfo()
                                                                        if report_info_name:
                                                                            report_info.name = report_info_name
                                                                            report_info.default_value = report_info_default_value
                                                                            report_info.report_model = report_save
                                                                            report_info.save()
                                                                            update_id_list.append(report_info.id)
                                                                current_report_info.exclude(
                                                                    id__in=update_id_list).update(
                                                                    state="9")

                                                                id = report_save.id
                                                    except Exception as e:
                                                        errors.append("修改失败。")
                                        else:
                                            errors.append('本次报表上传任务失败。')
        return render(request, 'report.html',
                      {'username': request.user.userinfo.fullname,
                       "report_type_list": report_type_list,
                       "all_app_list": all_app_list,
                       "errors": errors,
                       "id": id,
                       "pagefuns": getpagefuns(funid)})
    else:
        return HttpResponseRedirect("/login")


def report_app_index(request, funid):
    """
    应用报表管理
    """
    if request.user.is_authenticated():
        errors = []
        id = ""
        report_type_list = []
        adminapp = ""
        try:
            cur_fun = Fun.objects.filter(id=int(funid)).exclude(state='9')
            adminapp = cur_fun[0].app_id
        except:
            return HttpResponseRedirect("/index")

        # 下拉框选项
        c_dict_index_1 = DictIndex.objects.filter(
            id=7).exclude(state='9')
        if c_dict_index_1.exists():
            c_dict_index_1 = c_dict_index_1[0]
            dict_list1 = c_dict_index_1.dictlist_set.exclude(state="9")
            for i in dict_list1:
                report_type_list.append({
                    "report_name": i.name,
                    "report_type_id": i.id,
                })
        all_app = App.objects.exclude(state="9")
        all_app_list = []
        for app in all_app:
            all_app_list.append({
                "app_id": app.id,
                "app_name": app.name,
            })

        # 新增/修改报表模型
        if request.method == "POST":
            id = request.POST.get("id", "")
            name = request.POST.get("name", "")
            code = request.POST.get("code", "")
            report_type = request.POST.get("report_type", "")
            app = request.POST.get("app", "")
            sort = request.POST.get("sort", "")
            # 二进制文件数据
            my_file = request.FILES.get("report_file", None)

            file_name = my_file.name if my_file else ""

            # 报表信息组(键值对)的数量
            report_info_num = 0
            for key in request.POST.keys():
                if "report_info_" in key:
                    report_info_num += 1

            try:
                id = int(id)
            except:
                raise Http404()

            # 新增时提示导入文件
            if not my_file and id == 0:
                errors.append("请选择要导入的文件。")
            else:
                if if_contains_sign(file_name):
                    errors.append(r"""请注意文件命名格式，'\/"*?<>'符号文件不允许上传。""")
                else:
                    # 报表存储位置
                    myfilepath = settings.BASE_DIR + os.sep + "datacenter" + os.sep + "upload" + os.sep + "report_doc" + os.sep + file_name
                    # 判断数据库中文件存储记录
                    c_exist_model = ReportModel.objects.filter(file_name=file_name).exclude(state="9")

                    # 新增时判断是否存在，修改时覆盖，不需要判断
                    if c_exist_model.exists() and id == 0:
                        errors.append("该文件已存在,请勿重复上传。")
                    else:
                        if name.strip() == '':
                            errors.append('报表名称不能为空。')
                        else:
                            if code.strip() == '':
                                errors.append('报表编码不能为空。')
                            else:
                                if report_type.strip() == '':
                                    errors.append('报表类型不能为空。')
                                else:
                                    if app.strip() == '':
                                        errors.append('关联应用不能为空。')
                                    else:
                                        write_tag = False
                                        # 新增 或者 修改(且有my_file存在) 时写入文件
                                        if id == 0 or id != 0 and my_file:
                                            # 判断请求服务器下载文件条件是否满足
                                            # ps_script_path/report_file_path/web_server/report_server/username/password
                                            rs = ReportServer.objects.first()
                                            if not rs:
                                                errors.append('报表服务器参数未配置，报表上传失败。')
                                            elif not rs.report_server:
                                                errors.append('报表服务器地址未配置，报表上传失败。')
                                            elif not rs.username:
                                                errors.append('报表服务器用户名未配置，报表上传失败。')
                                            elif not rs.password:
                                                errors.append('报表服务器密码未配置，报表上传失败。')
                                            elif not rs.report_file_path:
                                                errors.append('报表存放路径未配置，报表上传失败。')
                                            else:
                                                try:
                                                    with open(myfilepath, 'wb+') as f:
                                                        for chunk in my_file.chunks():
                                                            f.write(chunk)
                                                except Exception as e:
                                                    print(e)
                                                    errors.append('文件上传失败。')
                                                else:
                                                    # 只要有文件写入，就发送请求
                                                    # 远程执行命令，令远程windows发送请求下载文件
                                                    pre_ps_path = os.path.join(rs.report_file_path, 'report_ps')
                                                    ps_script_path = os.path.join(pre_ps_path, 'request.ps1')
                                                    report_file_path = os.path.join(rs.report_file_path, file_name)
                                                    remote_ip = rs.report_server.split(':')[0]
                                                    remote_user = rs.username
                                                    remote_password = rs.password
                                                    remote_platform = "Windows"

                                                    # 判断ps脚本是否存在
                                                    # 若不存在，创建路径，写入文件
                                                    ps_check_cmd = r'if not exist {pre_ps_path} md {pre_ps_path}'.format(
                                                        pre_ps_path=pre_ps_path)
                                                    ps_script = ServerByPara(ps_check_cmd, remote_ip, remote_user,
                                                                             remote_password, remote_platform)
                                                    ps_result = ps_script.run("")

                                                    if ps_result['exec_tag'] == 1:
                                                        errors.append(ps_result['log'])
                                                    else:
                                                        # 写入脚本文件
                                                        ps_upload_cmd = 'echo param($a, $b) > %s &' % ps_script_path + \
                                                                        'echo $Response=Invoke-WebRequest -Uri $b >> %s &' % ps_script_path + \
                                                                        'echo try{ >> %s &' % ps_script_path + \
                                                                        'echo    [System.IO.File]::WriteAllBytes($a, $Response.Content) >> %s &' % ps_script_path + \
                                                                        'echo }catch{ >> %s &' % ps_script_path + \
                                                                        'echo   [System.Console]::WriteLine($_.Exception.Message) >> %s &' % ps_script_path + \
                                                                        'echo } >> %s &' % ps_script_path
                                                        ps_upload = ServerByPara(ps_upload_cmd, remote_ip, remote_user,
                                                                                 remote_password, remote_platform)
                                                        ps_upload_result = ps_upload.run("")

                                                        if ps_upload_result['exec_tag'] == 1:
                                                            errors.append(ps_upload_result['log'])
                                                        else:
                                                            # 判断报表路径是否存在
                                                            # 若不存在，提示不存在，报表上传失败
                                                            # 获取app_code
                                                            try:
                                                                cur_app = App.objects.get(id=int(app))
                                                            except:
                                                                write_tag = False
                                                                errors.append('应用不存在。')
                                                            else:
                                                                app_code = cur_app.code
                                                                aft_report_file_path = os.path.join(rs.report_file_path,
                                                                                                    str(app_code))
                                                                report_check_cmd = r'if not exist {report_file_path} md {report_file_path}'.format(
                                                                    report_file_path=aft_report_file_path)

                                                                rc = ServerByPara(report_check_cmd, remote_ip,
                                                                                  remote_user,
                                                                                  remote_password, remote_platform)
                                                                rc_result = rc.run("")

                                                                if rc_result['exec_tag'] == 1:
                                                                    errors.append(rc_result['log'])
                                                                else:
                                                                    # 获取本地IP
                                                                    try:
                                                                        web_server = socket.gethostbyname(
                                                                            socket.gethostname())
                                                                    except Exception as e:
                                                                        errors.append("获取服务器IP失败：%s" % e)
                                                                    else:
                                                                        url_visited = r"http://{web_server}/download_file?file_name={file_name}".format(
                                                                            web_server=web_server, file_name=file_name)
                                                                        remote_cmd = r'powershell.exe -ExecutionPolicy RemoteSigned -file "{0}" "{1}" "{2}"'.format(
                                                                            ps_script_path,
                                                                            os.path.join(aft_report_file_path,
                                                                                         file_name),
                                                                            url_visited)

                                                                        server_obj = ServerByPara(remote_cmd, remote_ip,
                                                                                                  remote_user,
                                                                                                  remote_password,
                                                                                                  remote_platform)
                                                                        result = server_obj.run("")
                                                                        if result["exec_tag"] == 0:
                                                                            write_tag = True
                                                                        else:
                                                                            errors.append(result['log'])

                                        if id != 0 and not my_file:
                                            write_tag = True

                                        # 远程文件下载成功
                                        if write_tag:
                                            # 新增报表模板
                                            if id == 0:
                                                all_report = ReportModel.objects.filter(
                                                    code=code).exclude(state="9")
                                                if all_report.exists():
                                                    errors.append('报表编码:' + code + '已存在。')
                                                else:
                                                    try:
                                                        report_save = ReportModel()
                                                        report_save.name = name
                                                        report_save.code = code
                                                        report_save.report_type = report_type
                                                        report_save.app_id = int(app)
                                                        report_save.file_name = file_name
                                                        report_save.sort = int(sort) if sort else None
                                                        report_save.save()

                                                        # 关联存储报表模板信息
                                                        if report_info_num:
                                                            range_num = int(report_info_num / 3)
                                                            for i in range(0, range_num):
                                                                report_info = ReportInfo()
                                                                report_info_name = request.POST.get(
                                                                    "report_info_name_%d" % (i + 1), "")
                                                                report_info_default_value = request.POST.get(
                                                                    "report_info_value_%d" % (i + 1), "")
                                                                if report_info_name:
                                                                    report_info.name = report_info_name
                                                                    report_info.default_value = report_info_default_value
                                                                    report_info.report_model = report_save
                                                                    report_info.save()

                                                        id = report_save.id
                                                    except:
                                                        errors.append('数据异常，请联系管理员!')
                                            # 修改报表模板
                                            else:
                                                all_report = ReportModel.objects.filter(code=code).exclude(
                                                    id=id).exclude(state="9")
                                                if all_report.exists():
                                                    errors.append('存储编码:' + code + '已存在。')
                                                else:
                                                    try:
                                                        report_save = ReportModel.objects.get(id=id)
                                                        report_save.name = name
                                                        report_save.code = code
                                                        report_save.report_type = report_type
                                                        report_save.app_id = int(app)
                                                        if my_file:
                                                            report_save.file_name = file_name
                                                        report_save.sort = int(sort) if sort else None
                                                        report_save.save()

                                                        # 修改报表信息关联
                                                        # 情况：报表信息组相对数据库中存储树，增加/减少/相同 一样
                                                        if report_info_num:
                                                            range_num = int(report_info_num / 3)
                                                            current_report_info = report_save.reportinfo_set.exclude(
                                                                state="9")

                                                            update_id_list = []
                                                            for i in range(0, range_num):
                                                                report_info_name = request.POST.get(
                                                                    "report_info_name_%d" % (i + 1), "")
                                                                report_info_default_value = request.POST.get(
                                                                    "report_info_value_%d" % (i + 1), "")
                                                                report_info_id = request.POST.get(
                                                                    "report_info_id_%d" % (i + 1), "")
                                                                report_info_id = int(
                                                                    report_info_id) if report_info_id else ""

                                                                if report_info_id:
                                                                    update_id_list.append(report_info_id)
                                                                    report_info = ReportInfo.objects.filter(
                                                                        id=report_info_id)
                                                                    if report_info.exists() and report_info_name:
                                                                        report_info = report_info[0]
                                                                        report_info.name = report_info_name
                                                                        report_info.default_value = report_info_default_value
                                                                        report_info.report_model = report_save
                                                                        report_info.save()
                                                                else:
                                                                    report_info = ReportInfo()
                                                                    if report_info_name:
                                                                        report_info.name = report_info_name
                                                                        report_info.default_value = report_info_default_value
                                                                        report_info.report_model = report_save
                                                                        report_info.save()
                                                                        update_id_list.append(report_info.id)
                                                            current_report_info.exclude(
                                                                id__in=update_id_list).update(
                                                                state="9")

                                                            id = report_save.id
                                                    except Exception as e:
                                                        errors.append("修改失败。")
                                        else:
                                            errors.append('本次上传报表任务失败。')
        return render(request, 'report_app.html',
                      {'username': request.user.userinfo.fullname,
                       "report_type_list": report_type_list,
                       "all_app_list": all_app_list,
                       "errors": errors,
                       "id": id,
                       "adminapp": adminapp,
                       "pagefuns": getpagefuns(funid)})
    else:
        return HttpResponseRedirect("/login")


def report_data(request):
    if request.user.is_authenticated():
        result = []
        search_app = request.GET.get('search_app', '')

        try:
            search_app = int(search_app)
        except Exception:
            pass

        all_report = ReportModel.objects.exclude(state="9").order_by("-if_template", "sort")

        # 当前应用下的所有报表+系统模板报表
        if search_app:
            template_report = all_report.filter(if_template=1)
            app_report = all_report.filter(app_id=search_app)

            all_report = template_report | app_report

        # if search_app != "":
        #     curadminapp = App.objects.get(id=int(search_app))
        #     all_report = all_report.filter(app=curadminapp)

        for report in all_report:
            # 报表类型
            report_type = report.report_type
            try:
                report_type_dict_list = DictList.objects.filter(id=int(report.report_type))
                if report_type_dict_list.exists():
                    report_type_dict_list = report_type_dict_list[0]
                    report_type = report_type_dict_list.name
            except:
                pass

            report_info_list = []
            current_report_info_set = report.reportinfo_set.exclude(state="9")
            if current_report_info_set.exists():
                for report_info in current_report_info_set:
                    report_info_list.append({
                        "report_info_name": report_info.name,
                        "report_info_value": report_info.default_value,
                        "report_info_id": int(report_info.id),
                    })
            result.append({
                "id": report.id,
                "name": report.name,
                "code": report.code,
                "file_name": report.file_name,
                "report_type": report_type,
                "report_type_id": int(report.report_type) if report.report_type else "",
                "app": report.app.name if report.app else "",
                "app_id": report.app.id if report.app else "",
                "report_type_num": report.report_type,
                "sort": report.sort,
                "report_info_list": report_info_list,
                "if_template": report.if_template,
            })

        return JsonResponse({"data": result})


def report_del(request):
    if request.user.is_authenticated():
        if 'id' in request.POST:
            id = request.POST.get('id', '')
            try:
                id = int(id)
            except:
                raise Http404()
            report = ReportModel.objects.filter(id=id)

            # 修改：删除远程服务器文件
            if report.exists():
                report = report[0]
                report.state = "9"
                report.save()

                # 删除关联report_info
                report_info_set = report.reportinfo_set.exclude(state="9")
                if report_info_set.exists():
                    for i in report_info_set:
                        i.state = "9"
                        i.save()

                c_file_name = report.file_name
                the_file_name = settings.BASE_DIR + os.sep + "datacenter" + os.sep + "upload" + os.sep + "report_doc" + os.sep + c_file_name
                if os.path.exists(the_file_name):
                    try:
                        os.remove(the_file_name)
                    except:
                        pass
                return HttpResponse(1)
            else:
                return HttpResponse(0)
        else:
            return HttpResponse(0)


def app_save(request):
    if request.user.is_authenticated():
        id = request.POST.get("id", "")
        app_name = request.POST.get("app_name", "")
        app_code = request.POST.get("app_code", "")
        remark = request.POST.get("remark", "")
        sort = request.POST.get("sort", "")
        work_data = []

        try:
            work_data = json.loads(request.POST.get("work_data", ""))
        except:
            pass
        try:
            id = int(id)
        except:
            raise Http404()
        result = {}

        if app_name.strip() == '':
            result["res"] = '应用名称不能为空。'
        else:
            if app_code.strip() == '':
                result["res"] = '应用编码不能为空。'
            else:
                if remark.strip() == '':
                    result["res"] = '说明不能为空。'
                else:
                    if not work_data:
                        result["res"] = '至少配置一个业务。'
                    else:
                        def save_work(app):
                            wd_list = []
                            for wd in work_data:
                                try:
                                    wd_id = int(wd[0])
                                except:
                                    work = Work()
                                    work.app = app
                                    work.name = wd[1]
                                    work.code = wd[2]
                                    work.remark = wd[3]
                                    if wd[4]:
                                        work.core = wd[4]
                                    if wd[5]:
                                        work.sort = int(wd[5])
                                    work.save()
                                    wd_list.append(work.id)
                                else:
                                    wd_list.append(wd_id)
                                    try:
                                        work = Work.objects.get(id=wd_id)
                                        work.name = wd[1]
                                        work.code = wd[2]
                                        work.remark = wd[3]
                                        if wd[4]:
                                            work.core = wd[4]
                                        if wd[5]:
                                            work.sort = int(wd[5])
                                        work.save()
                                    except:
                                        pass
                            app.work_set.exclude(id__in=wd_list).update(state='9')

                        if id == 0:
                            all_app = App.objects.filter(
                                code=app_code).exclude(state="9")
                            if (len(all_app) > 0):
                                result["res"] = '存储代码:' + app_code + '已存在。'
                            else:
                                app_save = App()
                                app_save.name = app_name
                                app_save.code = app_code
                                app_save.remark = remark
                                app_save.sort = int(sort) if sort else None
                                app_save.save()
                                save_work(app_save)
                                result["res"] = "保存成功。"
                                result["data"] = app_save.id
                        else:
                            all_app = App.objects.filter(code=app_code).exclude(
                                id=id).exclude(state="9")
                            if (len(all_app) > 0):
                                result["res"] = '存储代码:' + app_code + '已存在。'
                            else:
                                try:
                                    app_save = App.objects.get(id=id)
                                    app_save.name = app_name
                                    app_save.code = app_code
                                    app_save.remark = remark
                                    app_save.sort = int(sort) if sort else None
                                    app_save.save()
                                    save_work(app_save)
                                    result["res"] = "保存成功。"
                                    result["data"] = app_save.id
                                except Exception as e:
                                    print(e)
                                    result["res"] = "修改失败。"
        return JsonResponse(result)


def app_del(request):
    if request.user.is_authenticated():
        if 'id' in request.POST:
            id = request.POST.get('id', '')
            try:
                id = int(id)
            except:
                raise Http404()
            app = App.objects.get(id=id)
            app.state = "9"
            app.save()

            return HttpResponse(1)
        else:
            return HttpResponse(0)


def app_index(request, funid):
    """
    应用管理
    """
    if request.user.is_authenticated():
        return render(request, 'app.html',
                      {'username': request.user.userinfo.fullname,
                       "pagefuns": getpagefuns(funid)})
    else:
        return HttpResponseRedirect("/login")


def app_data(request):
    if request.user.is_authenticated():
        result = []

        all_app = App.objects.exclude(state="9").order_by("sort").values()
        all_work = Work.objects.exclude(state='9').order_by("sort").values()
        for app in all_app:
            work_list = []
            # 应用对应的所有业务
            for work in all_work:
                if app['id'] == work['app_id']:
                    tmp_list = [work['id'], work['name'], work['code'], work['remark'], work['core'], work['sort']]
                    work_list.append(tmp_list)

            result.append({
                "id": app['id'],
                "name": app['name'],
                "code": app['code'],
                "remark": app['remark'],
                "sort": app['sort'],
                "works": json.dumps(work_list, ensure_ascii=False),
            })
        return JsonResponse({"data": result})


def dictindex(request, funid):
    if request.user.is_authenticated():
        alldict = DictIndex.objects.order_by("sort").exclude(state="9")
        return render(request, 'dict.html',
                      {'username': request.user.userinfo.fullname,
                       "alldict": alldict, "pagefuns": getpagefuns(funid)})
    else:
        return HttpResponseRedirect("/login")


def dictsave(request):
    if 'dictid' in request.POST:
        result = {}
        dictid = request.POST.get('dictid', '')
        dictname = request.POST.get('dictname', '')
        dictsort = request.POST.get('dictsort', '')
        try:
            dictsort = int(dictsort)
        except:
            dictsort = 999999
        try:
            dictid = int(dictid.replace("dict_", ""))
        except:
            raise Http404()
        if dictname.strip() == '':
            result["res"] = '字典名称不能为空。'
        else:
            if dictid == 0:
                alldict = DictIndex.objects.filter(
                    name=dictname).exclude(state="9")
                if (len(alldict) > 0):
                    result["res"] = dictname + '已存在。'
                else:
                    dictsave = DictIndex()
                    dictsave.name = dictname
                    dictsave.sort = dictsort
                    dictsave.save()
                    dictsave = DictIndex.objects.filter(
                        name=dictname).exclude(state="9")
                    result["res"] = "新增成功。"
                    result["data"] = dictsave[0].id
            else:
                alldict = DictIndex.objects.filter(
                    name=dictname).exclude(id=dictid).exclude(state="9")
                if (len(alldict) > 0):
                    result["res"] = dictname + '已存在。'
                else:
                    try:
                        dictsave = DictIndex.objects.get(id=dictid)
                        dictsave.name = dictname
                        dictsave.sort = dictsort
                        dictsave.save()
                        result["res"] = "修改成功。"
                    except:
                        result["res"] = "修改失败。"
        return HttpResponse(json.dumps(result))


def dictselect(request):
    if request.method == 'GET':
        result = []
        dictid = request.GET.get('dictid', '')
        try:
            dictid = int(dictid.replace("dict_", ""))
        except:
            raise Http404()
        alldict = DictIndex.objects.get(id=dictid)
        allDictList = DictList.objects.order_by("sort").filter(
            dictindex=alldict).exclude(state="9")
        if (len(allDictList) > 0):
            for dict_list in allDictList:
                result.append(
                    {"id": dict_list.id, "name": dict_list.name, "sort": dict_list.sort})
        return HttpResponse(json.dumps(result))


def dictlistsave(request):
    if 'dictid' in request.POST:
        result = {}

        listid = request.POST.get('listid', '')
        dictid = request.POST.get('dictid', '')
        listname = request.POST.get('listname', '')
        listsort = request.POST.get('listsort', '')

        try:
            listsort = int(listsort)
        except:
            listsort = 999999
        try:
            dictid = int(dictid.replace("dict_", ""))
        except:
            raise Http404()
        try:
            listid = int(listid.replace("list_", ""))
        except:
            raise Http404()
        if listname.strip() == '':
            result["res"] = '条目名称不能为空。'
        else:
            alldict = DictIndex.objects.get(id=dictid)
            if listid == 0:

                alllist = DictList.objects.filter(
                    name=listname, dictindex=alldict).exclude(state="9")
                if (len(alllist) > 0):
                    result["res"] = listname + '已存在。'
                else:
                    listsave = DictList()
                    listsave.dictindex = alldict
                    listsave.name = listname
                    listsave.sort = listsort
                    listsave.save()
                    listsave = DictList.objects.filter(
                        name=listname, dictindex=alldict).exclude(state="9")
                    result["res"] = "新增成功。"
                    result["data"] = listsave[0].id
            else:
                alllist = DictList.objects.filter(name=listname).filter(dictindex=alldict).exclude(id=listid).exclude(
                    state="9")
                if (len(alllist) > 0):
                    result["res"] = listname + '已存在。'
                else:
                    try:
                        listsave = DictList.objects.get(id=listid)
                        listsave.name = listname
                        listsave.sort = listsort
                        listsave.save()
                        result["res"] = "修改成功。"
                    except:
                        result["res"] = "修改失败。"
        return HttpResponse(json.dumps(result))


def dictdel(request):
    if 'dictid' in request.POST:
        result = ""
        dictid = request.POST.get('dictid', '')
        try:
            dictid = int(dictid.replace("dict_", ""))
        except:
            raise Http404()
        alldict = DictIndex.objects.filter(id=dictid)
        if (len(alldict) > 0):
            dictsave = alldict[0]
            dictsave.state = "9"
            dictsave.save()
            result = "删除成功。"
        else:
            result = '字典不存在。'
        return HttpResponse(result)


def dictlistdel(request):
    if 'listid' in request.POST:
        result = ""
        listid = request.POST.get('listid', '')
        try:
            listid = int(listid.replace("list_", ""))
        except:
            raise Http404()
        alllist = DictList.objects.filter(id=listid)
        if (len(alllist) > 0):
            listsave = alllist[0]
            listsave.state = "9"
            listsave.save()
            result = "删除成功。"
        else:
            result = '条目不存在。'
        return HttpResponse(result)


def storage_index(request, funid):
    """
    存储配置
    """
    if request.user.is_authenticated():
        storage_type_list = []
        valid_time_list = []

        dict_list = DictList.objects.exclude(state='9', dictindex__state='9').values(
            'id', 'name', 'dictindex__id'
        )

        for dl in dict_list:
            if dl['dictindex__id'] == 4:
                # 存储类型
                storage_type_list.append({
                    "storage_name": dl['name'],
                    "storage_type_id": dl['id'],
                })
            if dl['dictindex__id'] == 3:
                # 有效时间
                valid_time_list.append({
                    "valid_time": dl['name'],
                    "valid_time_id": dl['id'],
                })

        return render(request, 'storage.html',
                      {'username': request.user.userinfo.fullname,
                       "storage_type_list": storage_type_list,
                       "valid_time_list": valid_time_list,
                       "pagefuns": getpagefuns(funid)})
    else:
        return HttpResponseRedirect("/login")


def storage_data(request):
    if request.user.is_authenticated():
        result = []
        all_storage = Storage.objects.exclude(state="9").order_by("sort")

        all_dict_list = DictList.objects.exclude(
            state='9').values('id', 'name')

        for storage in all_storage:
            storage_type = storage.storagetype
            storage_type_display = ""
            for dict in all_dict_list:
                if storage_type == str(dict['id']):
                    storage_type_display = dict['name']
                    break

            validtime = storage.validtime
            try:
                validtime_dict_list = DictList.objects.filter(id=int(storage.validtime))
                if validtime_dict_list.exists():
                    validtime_dict_list = validtime_dict_list[0]
                    validtime = validtime_dict_list.name
            except:
                pass

            result.append({
                "id": storage.id,
                "name": storage.name,
                "tablename": storage.tablename,
                "storagetype_num": storage_type,
                "validtime_num": storage.validtime,
                "storagetype": storage_type_display,
                "validtime": validtime,
                "sort": storage.sort,
            })
        return JsonResponse({"data": result})


def storage_save(request):
    if request.user.is_authenticated():
        id = request.POST.get("id", "")
        storage_name = request.POST.get("storage_name", "")
        table_name = request.POST.get("table_name", "")
        storage_type = request.POST.get("storage_type", "")
        valid_time = request.POST.get("valid_time", "")
        sort = request.POST.get("sort", "")

        try:
            id = int(id)
        except:
            raise Http404()

        result = {}

        if storage_name.strip() == '':
            result["res"] = '存储名称不能为空。'
        else:

            if table_name.strip() == '':
                result["res"] = '数据库表名不能为空。'
            else:
                if storage_type.strip() == '':
                    result["res"] = '存储类型不能为空。'
                else:
                    if valid_time.strip() == '':
                        result["res"] = '有效时间不能为空。'
                    else:
                        if id == 0:
                            all_storage = Storage.objects.filter(
                                name=storage_name).exclude(state="9")
                            if (len(all_storage) > 0):
                                result["res"] = '存储名称:' + \
                                                storage_name + '已存在。'
                            else:
                                try:
                                    storage_save = Storage()
                                    storage_save.name = storage_name
                                    storage_save.tablename = table_name
                                    storage_save.storagetype = storage_type
                                    storage_save.validtime = valid_time
                                    storage_save.sort = sort if sort else None
                                    storage_save.save()
                                    result["res"] = "保存成功。"
                                    result["data"] = storage_save.id
                                except Exception as e:
                                    print(e)
                                    result["res"] = "保存失败。"
                        else:
                            all_storage = Storage.objects.filter(name=storage_name).exclude(
                                id=id).exclude(state="9")
                            if (len(all_storage) > 0):
                                result["res"] = '存储名称:' + \
                                                storage_name + '已存在。'
                            else:
                                try:
                                    storage_save = Storage.objects.get(
                                        id=id)
                                    storage_save.name = storage_name
                                    storage_save.tablename = table_name
                                    storage_save.storagetype = storage_type
                                    storage_save.validtime = valid_time
                                    storage_save.sort = int(
                                        sort) if sort else None
                                    storage_save.save()
                                    result["res"] = "保存成功。"
                                    result["data"] = storage_save.id
                                except:
                                    result["res"] = "修改失败。"
    return JsonResponse(result)


def storage_del(request):
    if request.user.is_authenticated():
        if 'id' in request.POST:
            id = request.POST.get('id', '')
            try:
                id = int(id)
            except:
                raise Http404()
            storage = Storage.objects.get(id=id)
            storage.state = "9"
            storage.save()

            return HttpResponse(1)
        else:
            return HttpResponse(0)


def cycle_index(request, funid):
    """
    周期配置
    """
    if request.user.is_authenticated():
        return render(request, 'cycle.html',
                      {'username': request.user.userinfo.fullname,
                       "pagefuns": getpagefuns(funid)})
    else:
        return HttpResponseRedirect("/login")


def cycle_data(request):
    if request.user.is_authenticated():
        result = []

        all_cycle = Cycle.objects.exclude(state="9").order_by("sort")
        for cycle in all_cycle:
            schedule_type = cycle.schedule_type
            schedule_type_display = cycle.get_schedule_type_display()

            sub_cycles = cycle.subcycle_set.exclude(state="9")
            sub_cycle_data = []
            for sc in sub_cycles:
                sub_cycle_data.append({
                    "sub_cycle_id": sc.id,
                    "minutes": sc.minute,
                    "hours": sc.hour,
                    "per_week": sc.day_of_week,
                    "per_month": sc.day_of_month,
                })

            result.append({
                "id": cycle.id,
                "name": cycle.name,
                "sort": cycle.sort,
                "schedule_type": schedule_type,
                "schedule_type_display": schedule_type_display,
                "sub_cycle_data": sub_cycle_data
            })

        return JsonResponse({"data": result})


def cycle_save(request):
    if request.user.is_authenticated():
        id = request.POST.get("id", "")
        cycle_name = request.POST.get("cycle_name", "")
        sort = request.POST.get("sort", "")

        schedule_type = request.POST.get('schedule_type', '')

        sub_cycle = eval(request.POST.get('sub_cycle', '[]'))
        # [{'hours': '0', 'minutes': '00', 'per_month': '324', 'per_week': '', 'sub_cycle_id': '暂无'}]
        try:
            id = int(id)
        except:
            raise Http404()
        result = {}

        if cycle_name.strip() == '':
            result["res"] = '周期名称不能为空。'
        else:
            # 周期类型
            try:
                schedule_type = int(schedule_type)
            except ValueError as e:
                return JsonResponse({
                    "res": "周期类型未选择。"
                })
            if id == 0:
                all_cycle = Cycle.objects.filter(
                    name=cycle_name).exclude(state="9")
                if (len(all_cycle) > 0):
                    result["res"] = '存储代码:' + cycle_name + '已存在。'
                else:
                    try:
                        with transaction.atomic():
                            cycle_save = Cycle()
                            cycle_save.name = cycle_name
                            cycle_save.schedule_type = schedule_type
                            cycle_save.sort = int(sort) if sort else None
                            cycle_save.save()
                            for sc in sub_cycle:
                                sc_data = {
                                    "hour": sc["hours"],
                                    "minute": sc["minutes"],
                                    "day_of_week": sc["per_week"],
                                    "day_of_month": sc["per_month"],
                                }
                                cycle_save.subcycle_set.create(**sc_data)
                    except Exception as e:
                        result["res"] = "保存失败：{0}".format(e)
                    else:
                        result["res"] = "保存成功。"
                        result["data"] = cycle_save.id
            else:
                all_cycle = Cycle.objects.filter(name=cycle_name).exclude(
                    id=id).exclude(state="9")
                if (len(all_cycle) > 0):
                    result["res"] = '存储名称:' + cycle_name + '已存在。'
                else:
                    try:
                        with transaction.atomic():
                            cycle_save = Cycle.objects.get(id=id)
                            cycle_save.name = cycle_name
                            cycle_save.schedule_type = schedule_type
                            cycle_save.sort = int(
                                sort) if sort else None
                            cycle_save.save()

                            # 删除原有而后不存在的
                            # 原有的ID与现在的ID校对 ID不存在的删除
                            sc_id_list = [int(sc["sub_cycle_id"]) for sc in sub_cycle if sc["sub_cycle_id"] != "暂无"]
                            existed_sub_cycles = cycle_save.subcycle_set.exclude(state="9")
                            for esc in existed_sub_cycles:
                                if esc.id not in sc_id_list:
                                    esc.state = "9"
                                    esc.save()

                            for sc in sub_cycle:
                                sc_data = {
                                    "hour": sc["hours"],
                                    "minute": sc["minutes"],
                                    "day_of_week": sc["per_week"],
                                    "day_of_month": sc["per_month"],
                                }
                                # add/edit
                                if sc["sub_cycle_id"] == "暂无":
                                    cycle_save.subcycle_set.create(**sc_data)
                                else:
                                    sub_cycle_id = int(sc["sub_cycle_id"])
                                    SubCycle.objects.exclude(state="9").filter(id=sub_cycle_id).update(**sc_data)
                    except Exception as e:
                        print(e)
                        result["res"] = "修改失败:{0}".format(e)
                    else:
                        result["res"] = "保存成功。"
                        result["data"] = cycle_save.id
        return JsonResponse(result)


def cycle_del(request):
    if request.user.is_authenticated():
        if 'id' in request.POST:
            id = request.POST.get('id', '')
            try:
                id = int(id)
            except:
                raise Http404()
            cycle = Cycle.objects.get(id=id)
            cycle.state = "9"
            cycle.save()

            return HttpResponse(1)
        else:
            return HttpResponse(0)


def get_select_source_type(temp_source_type=None):
    try:
        temp_source_type = int(temp_source_type)
    except:
        pass
    c_dict_index = DictIndex.objects.filter(id=2).exclude(state='9')
    if c_dict_index.exists():
        c_dict_index = c_dict_index[0]
        dict_list = c_dict_index.dictlist_set.exclude(state="9")
        source_type_list = []
        for i in dict_list:
            source_type_list.append({
                "source_type_id": i.id,
                "source_type": i.name,
                "source_if_selected": "selected" if temp_source_type == i.id else "",
            })
    else:
        source_type_list = []
    return source_type_list


def source_index(request, funid):
    """
    数据源配置
    :param request:
    :return:
    """
    if request.user.is_authenticated():
        try:
            errors = []
            selectid = ""
            id = ""
            pid = ""
            title = ""
            code = ""
            name = ""
            connection = ""

            hiddendiv = "hidden"
            # 数据源类型
            source_type_list = get_select_source_type()

            # 新增/保存/修改
            if request.method == "POST":
                hiddendiv = ""
                id = request.POST.get('id', '')
                pid = request.POST.get('pid', '')
                name = request.POST.get('name', '')
                code = request.POST.get('code', '')
                connection = request.POST.get('connection', '')
                sourcetype = request.POST.get('sourcetype', '')

                source_type_list = get_select_source_type(
                    temp_source_type=sourcetype)

                try:
                    id = int(id)
                except:
                    raise Http404()
                try:
                    pid = int(pid)
                except:
                    raise Http404()
                if id == 0:
                    selectid = pid
                    title = "新建"
                else:
                    selectid = id
                    title = name

                if code.strip() == '':
                    errors.append('数据源代码不能为空。')
                else:
                    if name.strip() == '':
                        errors.append('数据源名称不能为空。')
                    else:
                        if connection.strip() == '':
                            errors.append('连接符不能为空。')
                        else:
                            if sourcetype.strip() == '':
                                errors.append('数据源类型不能为空。')
                            else:
                                try:
                                    # 新增步骤
                                    if id == 0:
                                        try:
                                            pid = int(pid)
                                        except:
                                            pid = None
                                            max_sort_from_pnode = \
                                                Source.objects.exclude(state="9").filter(type='').filter(
                                                    pnode_id=None).aggregate(
                                                    Max("sort"))[
                                                    "sort__max"]
                                        else:
                                            max_sort_from_pnode = \
                                                Source.objects.exclude(state="9").filter(type='').filter(
                                                    pnode_id=pid).aggregate(
                                                    Max("sort"))[
                                                    "sort__max"]

                                        # 当前没有父节点
                                        if max_sort_from_pnode or max_sort_from_pnode == 0:
                                            my_sort = max_sort_from_pnode + 1
                                        else:
                                            my_sort = 0

                                        source = Source()
                                        source.name = name
                                        source.connection = connection
                                        source.code = code
                                        source.sort = my_sort
                                        source.sourcetype = sourcetype
                                        source.pnode_id = pid
                                        source.save()

                                        id = source.id
                                        title = name
                                        selectid = id
                                    else:
                                        source = Source.objects.filter(id=id)
                                        if source.exists():
                                            source = source[0]
                                            source.name = name
                                            source.code = code
                                            source.connection = connection
                                            source.sourcetype = sourcetype
                                            source.save()

                                            title = name
                                        else:
                                            errors.append(
                                                "当前资源不存在，无法修改，请联系客服！")
                                except:
                                    errors.append('保存失败。')

            # 加载树
            treedata = []
            rootnodes = Source.objects.order_by(
                "sort").filter(pnode=None).exclude(state="9").filter(type='')

            if len(rootnodes) > 0:
                for rootnode in rootnodes:
                    root = dict()
                    root["text"] = rootnode.name
                    root["id"] = rootnode.id

                    root["data"] = {
                        "code": rootnode.code,
                        "sourcetype": rootnode.sourcetype,
                        "connection": rootnode.connection,
                        "sort": rootnode.sort,
                        "verify": "first_node",
                    }
                    root["children"] = get_source_tree(
                        rootnode, selectid)
                    root["state"] = {"opened": True}
                    treedata.append(root)

            treedata = json.dumps(treedata)
            return render(request, 'source.html',
                          {'username': request.user.userinfo.fullname,
                           "treedata": treedata,
                           "title": title,
                           "errors": errors,
                           "source_type_list": source_type_list,
                           # 表单默认数据
                           "hiddendiv": hiddendiv,
                           "id": id,
                           "pid": pid,
                           "code": code,
                           "name": name,
                           "connection": connection,
                           "pagefuns": getpagefuns(funid)})
        except Exception as e:
            print(e)
            return HttpResponseRedirect("/index")
    else:
        return HttpResponseRedirect("/login")


def get_source_tree(parent, selectid):
    nodes = []
    children = parent.children.exclude(state="9").order_by("sort").exclude(state="9")
    for child in children:
        node = dict()
        node["text"] = child.name
        node["id"] = child.id
        node["children"] = get_source_tree(child, selectid)
        node["data"] = {
            "code": child.code,
            "sourcetype": child.sourcetype,
            "connection": child.connection,
            "sort": child.sort,
        }
        try:
            if int(selectid) == child.id:
                node["state"] = {"selected": True}
        except:
            pass
        nodes.append(node)
    return nodes


def del_source(request):
    if request.user.is_authenticated():
        if 'id' in request.POST:
            id = request.POST.get('id', '')
            try:
                id = int(id)
            except:
                raise Http404()
            all_source = Source.objects.filter(id=id)
            if all_source.exists():
                all_source = all_source[0]
                sort = all_source.sort
                p_source = all_source.pnode
                all_source.state = 9
                all_source.save()
                sort_source = Source.objects.filter(pnode=p_source).filter(
                    sort__gt=sort).exclude(state="9").filter(type='')
                if sort_source.exists():
                    for sortstep in sort_source:
                        try:
                            sortstep.sort = sortstep.sort - 1
                            sortstep.save()
                        except:
                            pass

                return HttpResponse(1)
            else:
                return HttpResponse(0)


def move_source(request):
    if request.user.is_authenticated():
        if 'id' in request.POST:
            id = request.POST.get('id', '')
            parent = request.POST.get('parent', '')
            old_parent = request.POST.get('old_parent', '')
            old_position = request.POST.get('old_position', '')
            position = request.POST.get('position', '')
            try:
                id = int(id)
            except:
                raise Http404()
            try:
                parent = int(parent)
            except:
                parent = None
            try:
                old_parent = int(old_parent)
            except:
                old_parent = None
            try:
                old_position = int(old_position)
            except:
                raise Http404()
            try:
                position = int(position)
            except:
                raise Http404()

            cur_source_obj = \
                Source.objects.filter(pnode_id=old_parent).filter(
                    sort=old_position).exclude(state="9").filter(type='')[0]
            cur_source_obj.sort = position
            cur_source_id = cur_source_obj.id
            cur_source_obj.save()
            # 同一pnode
            if parent == old_parent:
                # 向上拽
                source_under_pnode = Source.objects.filter(pnode_id=old_parent).exclude(state="9").filter(
                    sort__gte=position,
                    sort__lt=old_position).exclude(id=cur_source_id).filter(type='')
                for source in source_under_pnode:
                    source.sort += 1
                    source.save()

                # 向下拽
                source_under_pnode = Source.objects.filter(pnode_id=old_parent).exclude(state="9").filter(
                    sort__gt=old_position, sort__lte=position).exclude(id=cur_source_id).filter(type='')
                for source in source_under_pnode:
                    source.sort -= 1
                    source.save()

            # 向其他节点拽
            else:
                # 原来pnode下
                old_source = Source.objects.filter(pnode_id=old_parent).exclude(state="9").filter(
                    sort__gt=old_position).exclude(id=cur_source_id).filter(type='')
                for step in old_source:
                    step.sort -= 1
                    step.save()
                # 后来pnode下
                cur_source = Source.objects.filter(pnode_id=parent).exclude(state="9").filter(
                    sort__gte=position).exclude(
                    id=cur_source_id).filter(type='')
                for source in cur_source:
                    source.sort += 1
                    source.save()
            # pnode
            if parent:
                parent_source = Source.objects.get(id=parent)
            else:
                parent_source = None
            mystep = Source.objects.get(id=id)
            try:
                mystep.pnode = parent_source
                mystep.save()
            except:
                pass

            if parent != old_parent:
                if parent == None:
                    return HttpResponse(" ^ ")
                else:
                    return HttpResponse(parent_source.name + "^" + str(parent_source.id))
            else:
                return HttpResponse("0")


def target_index(request, funid):
    """
    指标管理
        过滤条件：
            管理应用
            查询应用

            操作类型
            周期类型
            业务类型
            机组 unit

            DictIndex 字典名称 >> DictList 字典条目
    """
    if request.user.is_authenticated():
        app_list = []
        operation_type_list = []
        cycle_type_list = []
        business_type_list = []
        unit_list = []
        source_list = []
        cycle_list = []
        storage_list = []

        applist = App.objects.all().exclude(state='9')
        for i in applist:
            # 业务
            works = i.work_set.exclude(state='9').values('id', 'name', 'core')

            app_list.append({
                "app_name": i.name,
                "app_id": i.id,
                "works": works,
            })

        c_dict_index_1 = DictIndex.objects.filter(
            id=1).exclude(state='9')
        if c_dict_index_1.exists():
            c_dict_index_1 = c_dict_index_1[0]
            dict_list1 = c_dict_index_1.dictlist_set.exclude(state="9")
            for i in dict_list1:
                operation_type_list.append({
                    "operation_type_name": i.name,
                    "operation_type_id": i.id,
                })

        c_dict_index_2 = DictIndex.objects.filter(
            id=12).exclude(state='9')
        if c_dict_index_2.exists():
            c_dict_index_2 = c_dict_index_2[0]
            dict_list2 = c_dict_index_2.dictlist_set.exclude(state="9")
            for i in dict_list2:
                cycle_type_list.append({
                    "cycle_type_name": i.name,
                    "cycle_type_id": i.id,
                })

        c_dict_index_3 = DictIndex.objects.filter(
            id=5).exclude(state='9')
        if c_dict_index_3.exists():
            c_dict_index_3 = c_dict_index_3[0]
            dict_list3 = c_dict_index_3.dictlist_set.exclude(state="9")
            for i in dict_list3:
                business_type_list.append({
                    "business_type_name": i.name,
                    "business_type_id": i.id,
                })

        c_dict_index_4 = DictIndex.objects.filter(
            id=6).exclude(state='9')
        if c_dict_index_4.exists():
            c_dict_index_4 = c_dict_index_4[0]
            dict_list4 = c_dict_index_4.dictlist_set.exclude(state="9")
            for i in dict_list4:
                unit_list.append({
                    "unit_name": i.name,
                    "unit_id": i.id,
                })
        sourcelist = Source.objects.all().exclude(state='9').exclude(pnode=None).filter(type='')
        for i in sourcelist:
            source_list.append({
                "source_name": i.name,
                "source_id": i.id,
            })

        cyclelist = Cycle.objects.all().exclude(state='9')
        for i in cyclelist:
            cycle_list.append({
                "cycle_name": i.name,
                "cycle_id": i.id,
            })

        storagelist = Storage.objects.all().exclude(state='9')

        all_dict_list = DictList.objects.exclude(state='9').values('id', 'name')

        for i in storagelist:
            storage_type = i.storagetype
            storage_type_display = ""
            for dict in all_dict_list:
                if storage_type == str(dict['id']):
                    storage_type_display = dict['name']
                    break

            storage_list.append({
                "storage_name": i.name,
                "storage_id": i.id,
                'storage_type': storage_type_display,
                "tablename": i.tablename,
            })

        # 加权指标
        weight_targets = Target.objects.exclude(state='9').values('id', 'name', 'code')
        return render(request, 'target.html',
                      {'username': request.user.userinfo.fullname,
                       "app_list": app_list,
                       "operation_type_list": operation_type_list,
                       "cycle_type_list": cycle_type_list,
                       "business_type_list": business_type_list,
                       "unit_list": unit_list,
                       "source_list": source_list,
                       "cycle_list": cycle_list,
                       "storage_list": storage_list,
                       "weight_targets": weight_targets,
                       "pagefuns": getpagefuns(funid)})
    else:
        return HttpResponseRedirect("/login")


def load_weight_targets(request):
    if request.user.is_authenticated():
        app_id = request.POST.get('app_id', '')
        weight_target_list = []
        try:
            app_id = int(app_id)
        except:
            # 加权指标
            weight_targets = Target.objects.exclude(state='9').values('id', 'name', 'code')
        else:
            weight_targets = Target.objects.filter(adminapp_id=app_id).exclude(state='9').values('id', 'name', 'code')

        weight_target_list = [{"id": w['id'], "text": "{name}({code})".format(name=w['name'], code=w['code'])} for w in
                              weight_targets]
        return JsonResponse({'data': str(weight_target_list)})
    else:
        return HttpResponseRedirect('/login')


def target_data(request):
    if request.user.is_authenticated():
        result = []
        search_adminapp = request.GET.get('search_adminapp', '')
        search_app = request.GET.get('search_app', '')
        search_operationtype = request.GET.get('search_operationtype', '')
        search_cycletype = request.GET.get('search_cycletype', '')
        search_businesstype = request.GET.get('search_businesstype', '')
        search_unit = request.GET.get('search_unit', '')
        search_app_noselect = request.GET.get('search_app_noselect', '')
        datatype = request.GET.get('datatype', '')
        works = request.GET.get('works', '')

        all_target = Target.objects.exclude(state="9").order_by("sort").select_related(
            "adminapp", "storage", "work"
        ).prefetch_related('app')
        if search_adminapp != "":
            if search_adminapp == 'null':
                all_target = all_target.filter(adminapp=None)
            else:
                curadminapp = App.objects.get(id=int(search_adminapp))
                all_target = all_target.filter(adminapp=curadminapp)
        if search_app != "":
            curadminapp = App.objects.get(id=int(search_app))
            curapp = App.objects.filter(id=int(search_app))
            all_target = all_target.exclude(adminapp=curadminapp).filter(app__in=curapp)

        try:
            search_app_noselect = int(search_app_noselect)
        except:
            pass
        else:
            # 过滤查询指标
            # 剔除当前核心业务的指标
            all_target = all_target.filter((~Q(adminapp__id=search_app_noselect) & ~Q(app__id=search_app_noselect)) | (
                (~Q(work__core='是') & ~Q(app__id=search_app_noselect) & Q(adminapp__id=search_app_noselect))))

        if search_operationtype != "":
            all_target = all_target.filter(operationtype=search_operationtype)
        if search_cycletype != "":
            all_target = all_target.filter(cycletype=search_cycletype)
        if search_businesstype != "":
            all_target = all_target.filter(businesstype=search_businesstype)
        if search_unit != "":
            all_target = all_target.filter(unit=search_unit)
        if datatype != "":
            all_target = all_target.filter(datatype=datatype)
        try:
            works = int(works)
            all_target = all_target.filter(work_id=works)
        except:
            pass

        all_dict_list = DictList.objects.exclude(state='9').values('id', 'name')
        all_works = Work.objects.exclude(state='9').values('id', 'name', 'app_id')

        for target in all_target:
            operationtype = target.operationtype
            if operationtype:
                for dict in all_dict_list:
                    if operationtype == str(dict['id']):
                        operationtype = dict['name']
                        break

            cycletype = target.cycletype
            if cycletype:
                for dict in all_dict_list:
                    if cycletype == str(dict['id']):
                        cycletype = dict['name']
                        break

            businesstype = target.businesstype
            if businesstype:
                for dict in all_dict_list:
                    if businesstype == str(dict['id']):
                        businesstype = dict['name']
                        break

            unit = target.unit
            if unit:
                for dict in all_dict_list:
                    if unit == str(dict['id']):
                        unit = dict['name']
                        break

            # 查询应用
            applist = []
            for my_app in target.app.all():
                applist.append(my_app.id)

            adminapp_name = ""
            try:
                adminapp_name = target.adminapp.name
            except:
                pass

            # 存储类型
            storage_type_display = ""
            storage = target.storage
            if storage:
                storage_type = storage.storagetype
                if storage_type:
                    for dict in all_dict_list:
                        if storage_type == str(dict['id']):
                            storage_type_display = dict['name']
                            break

            # 根据adminapp过滤出业务，并选中的业务
            work_selected = target.work.id if target.work else ''
            work_selected_name = target.work.name if target.work else ''
            admin_app = target.adminapp
            if admin_app:
                works = [work for work in all_works if work['app_id'] == admin_app.id]

            result.append({
                "operationtype_name": operationtype,
                "cycletype_name": cycletype,
                "businesstype_name": businesstype,
                "unit_name": unit,
                "adminapp_name": adminapp_name,
                "id": target.id,
                "name": target.name,
                "code": target.code,
                "operationtype": target.operationtype,
                "cycletype": target.cycletype,
                "businesstype": target.businesstype,
                "unit": target.unit,
                "adminapp": target.adminapp_id,
                "app": applist,
                "magnification": target.magnification,
                "digit": target.digit,
                "datatype": target.datatype,
                "cumulative": target.cumulative,
                "weight_target": target.weight_target.id if target.weight_target else '',

                "upperlimit": target.upperlimit,
                "lowerlimit": target.lowerlimit,
                "formula": target.formula,
                "cycle": target.cycle_id if target.cycle_id else "",
                "source": target.source_id,
                "source_content": target.source_content,
                "storage": target.storage_id,

                # 行、列判断是否展示存储标识
                "storage_type": storage_type_display,

                "storagefields": target.storagefields,
                "storagetag": target.storagetag,
                "sort": target.sort,
                "state": target.state,
                "remark": target.remark,

                'work_selected': work_selected,
                'work_selected_name': work_selected_name,
                'works': str(works),
                "unity": target.unity,
                "is_repeat": target.is_repeat,
                "data_from": target.data_from,

                "if_push": target.if_push,
                # "push_config": json.dumps(target.push_config if target.push_config else {}),
                "push_config": target.push_config.replace('"', '\\\"').replace("\'", '"') if target.push_config else "",
                # "push_config": target.push_config.replace('"', '\"') if target.push_config else "",
            })
        return JsonResponse({"data": result})


def target_formula_data(request):
    if request.user.is_authenticated():
        all_target = Target.objects.exclude(state="9")
        all_constant = Constant.objects.exclude(state="9")
        formula_analysis_data = {}
        for target in all_target:
            analysis_code = target.code
            analysis_name = target.name
            formula_analysis_data[analysis_code] = analysis_name
        for constant in all_constant:
            analysis_code = constant.code
            analysis_name = constant.name
            formula_analysis_data[analysis_code] = analysis_name
        return HttpResponse(json.dumps(formula_analysis_data, ensure_ascii=False))


def target_save(request):
    if request.user.is_authenticated():
        id = request.POST.get("id", "")
        name = request.POST.get("name", "")
        code = request.POST.get("code", "")
        operationtype = request.POST.get("operationtype", "")
        cycletype = request.POST.get("cycletype", "")
        businesstype = request.POST.get("businesstype", "")
        unit = request.POST.get("unit", "")

        adminapp = request.POST.get("adminapp", "")
        app_list = request.POST.getlist('app[]')
        datatype = request.POST.get("datatype", "")
        magnification = request.POST.get("magnification", "")
        digit = request.POST.get("digit", "")
        upperlimit = request.POST.get("upperlimit", "")
        lowerlimit = request.POST.get("lowerlimit", "")
        cumulative = request.POST.get("cumulative", "")
        weight_target = request.POST.get("weight_target", "")
        sort = request.POST.get("sort", "")

        formula = request.POST.get("formula", "")

        cycle = request.POST.get("cycle", "")
        source = request.POST.get("source", "")

        source_content = request.POST.get("source_content", "")

        storage = request.POST.get("storage", "")
        storagetag = request.POST.get("storagetag", "")
        storagefields = request.POST.get("storagefields", "")

        is_repeat = request.POST.get("is_repeat", "")
        savetype = request.POST.get("savetype", "")

        works = request.POST.get('works', '')
        unity = request.POST.get('unity', '')

        data_from = request.POST.get('data_from', '')
        calculate_source = request.POST.get('calculate_source', '')
        calculate_content = request.POST.get('calculate_content', '')

        if_push = request.POST.get('if_push', '')
        push_config = request.POST.get('push_config', '')

        try:
            push_config = json.loads(push_config)
        except:
            pass
        # {'dest_fields': ['b', 'd', 'werwer'], 'origin_source': '2', 'constraint_fields': ['rfe'], 'dest_table': 'reffa', 'origin_fields': ['a', 'c', 'wewer']}

        all_app = App.objects.exclude(state="9")
        all_cycle = Cycle.objects.exclude(state="9")
        all_source = Source.objects.exclude(state="9").filter(type='')
        all_storage = Storage.objects.exclude(state="9")

        try:
            id = int(id)
        except:
            raise Http404()

        result = {}

        if not name.strip():
            result["res"] = '指标名称不能为空。'
        elif not code.strip():
            result["res"] = '指标代码不能为空。'
        elif not operationtype.strip():
            result["res"] = '操作类型不能为空。'
        elif not cycletype.strip():
            result["res"] = '周期类型不能为空。'
        elif not businesstype.strip():
            result["res"] = '业务类型不能为空。'
        elif not unit.strip():
            result["res"] = '机组不能为空。'
        elif not datatype.strip():
            result["res"] = '数据类型不能为空。'
        else:
            if datatype.strip() == 'numbervalue':
                if not magnification:
                    result["res"] = '数据类型为数值时，倍率不能为空。'
                    return JsonResponse(result)
                if not digit:
                    result["res"] = '数据类型为数值时，保留位数不能为空。'
                    return JsonResponse(result)
            if operationtype == '17' and not data_from:
                result["res"] = '操作类型为数据计算时，必须选择数据来源。'
            else:
                if id == 0:
                    all_target = Target.objects.filter(code=code).exclude(state="9")
                    all_constant = Constant.objects.filter(code=code).exclude(state="9")
                    if (len(all_target) > 0):
                        result["res"] = '指标代码:' + \
                                        code + '已存在。'
                    else:
                        if (len(all_constant) > 0):
                            result["res"] = '常数库内已存在:' + code + '。'
                        else:
                            target_save = Target()
                            target_save.name = name
                            target_save.code = code
                            target_save.operationtype = operationtype
                            target_save.cycletype = cycletype
                            target_save.businesstype = businesstype
                            target_save.unit = unit
                            target_save.unity = unity
                            if data_from:
                                target_save.data_from = data_from

                            # 业务
                            try:
                                works = int(works)
                            except:
                                pass
                            else:
                                target_save.work_id = works

                            if datatype == 'numbervalue':
                                try:
                                    target_save.magnification = float(magnification)
                                except:
                                    pass
                                try:
                                    target_save.digit = int(digit)
                                except:
                                    pass
                                try:
                                    target_save.upperlimit = float(upperlimit)
                                except:
                                    pass
                                try:
                                    target_save.lowerlimit = float(lowerlimit)
                                except:
                                    pass
                                target_save.cumulative = cumulative
                                if cumulative == '3':
                                    try:
                                        weight_target = int(weight_target)
                                    except:
                                        weight_target = None
                                    target_save.weight_target_id = weight_target
                                else:
                                    target_save.weight_target_id = None
                            target_save.datatype = datatype
                            try:
                                app_id = int(adminapp)
                                my_app = all_app.get(id=app_id)
                                target_save.adminapp = my_app
                            except:
                                pass

                            try:
                                target_save.sort = int(sort)
                            except:
                                pass
                            # 计算
                            if operationtype == '17':
                                target_save.formula = formula
                                target_save.source_content = calculate_content
                                try:
                                    calculate_source = int(calculate_source)
                                except:
                                    calculate_source = None
                                finally:
                                    target_save.source_id = calculate_source
                            # 电表走字/提取
                            if operationtype in ['1', '16'] and savetype != 'app':
                                # 提取：推送配置
                                if operationtype == "16":
                                    if if_push == '1':
                                        target_save.push_config = str(push_config)
                                    target_save.if_push = if_push

                                try:
                                    cycle_id = int(cycle)
                                    my_cycle = all_cycle.get(id=cycle_id)
                                    target_save.cycle = my_cycle
                                except:
                                    target_save.cycle = None
                                try:
                                    source_id = int(source)
                                    my_source = all_source.get(id=source_id)
                                    target_save.source = my_source
                                except:
                                    pass

                                target_save.source_content = source_content
                                try:
                                    target_save.is_repeat = int(is_repeat)
                                except:
                                    pass
                                try:
                                    storage_id = int(storage)
                                    my_storage = all_storage.get(id=storage_id)
                                    target_save.storage = my_storage
                                except:
                                    pass
                                target_save.storagetag = storagetag
                                target_save.storagefields = storagefields
                            target_save.save()
                            # 存入多对多app
                            if savetype != 'app':
                                for app_id in app_list:
                                    try:
                                        app_id = int(app_id)
                                        my_app = all_app.get(id=app_id)
                                        target_save.app.add(my_app)
                                    except:
                                        pass
                            result["res"] = "保存成功。"
                            result["data"] = target_save.id
                else:
                    # 指标修改保存前，查看指标类型与本次类型是否相同，若不同：将该指标所有数据迁移至新的表中
                    try:
                        c_target = Target.objects.exclude(state="9").get(id=id)
                    except:
                        result["res"] = "指标不存在。"
                    else:
                        status, info = migrate_data_before_target_changed(c_target, operationtype)
                        if status == 0:
                            result["res"] = info
                        else:
                            all_target = Target.objects.filter(code=code).exclude(id=id).exclude(
                                state="9")
                            all_constant = Constant.objects.filter(code=code).exclude(state="9")
                            if (len(all_target) > 0):
                                result["res"] = '指标代码:' + \
                                                code + '已存在。'
                            else:
                                if (len(all_constant) > 0):
                                    result["res"] = '常数库内已存在:' + code + '。'
                                else:
                                    try:
                                        target_save = Target.objects.get(
                                            id=id)
                                        target_save.name = name
                                        target_save.code = code
                                        target_save.operationtype = operationtype
                                        target_save.cycletype = cycletype
                                        target_save.businesstype = businesstype
                                        target_save.unit = unit
                                        target_save.unity = unity
                                        if data_from:
                                            target_save.data_from = data_from

                                        # 业务
                                        try:
                                            works = int(works)
                                        except:
                                            pass
                                        else:
                                            target_save.work_id = works

                                        if datatype == 'numbervalue':
                                            try:
                                                target_save.magnification = float(magnification)
                                            except:
                                                pass
                                            try:
                                                target_save.digit = int(digit)
                                            except:
                                                pass
                                            try:
                                                target_save.upperlimit = float(upperlimit)
                                            except:
                                                pass
                                            try:
                                                target_save.lowerlimit = float(lowerlimit)
                                            except:
                                                pass
                                            target_save.cumulative = cumulative
                                            if cumulative == '3':
                                                try:
                                                    weight_target = int(weight_target)
                                                except:
                                                    weight_target = None
                                                target_save.weight_target_id = weight_target
                                            else:
                                                target_save.weight_target_id = None

                                        target_save.datatype = datatype
                                        try:
                                            app_id = int(adminapp)
                                            my_app = all_app.get(id=app_id)
                                            target_save.adminapp = my_app
                                        except:
                                            pass

                                        try:
                                            target_save.sort = int(sort)
                                        except:
                                            pass
                                        if operationtype == '17':
                                            target_save.formula = formula
                                            target_save.source_content = calculate_content
                                            try:
                                                calculate_source = int(calculate_source)
                                            except:
                                                calculate_source = None
                                            finally:
                                                target_save.source_id = calculate_source
                                        if operationtype in ['1', '16'] and savetype != 'app':
                                            if operationtype == "16":
                                                if if_push == '1':
                                                    target_save.push_config = str(push_config)
                                                target_save.if_push = if_push

                                            try:
                                                cycle_id = int(cycle)
                                                my_cycle = all_cycle.get(id=cycle_id)
                                                target_save.cycle = my_cycle
                                            except:
                                                target_save.cycle = None
                                            try:
                                                source_id = int(source)
                                                my_source = all_source.get(id=source_id)
                                                target_save.source = my_source
                                            except:
                                                pass

                                            target_save.source_content = source_content
                                            try:
                                                target_save.is_repeat = int(is_repeat)
                                            except:
                                                pass
                                            try:
                                                storage_id = int(storage)
                                                my_storage = all_storage.get(id=storage_id)
                                                target_save.storage = my_storage
                                            except:
                                                pass
                                            target_save.storagetag = storagetag
                                            target_save.storagefields = storagefields
                                        target_save.save()
                                        # 存入多对多app
                                        if savetype != 'app':
                                            target_save.app.clear()
                                            for app_id in app_list:
                                                try:
                                                    app_id = int(app_id)
                                                    my_app = all_app.get(id=app_id)
                                                    target_save.app.add(my_app)
                                                except:
                                                    pass
                                        result["res"] = "保存成功。"
                                        result["data"] = target_save.id
                                    except Exception as e:
                                        result["res"] = "修改失败。"

        return JsonResponse(result)


def target_del(request):
    if request.user.is_authenticated():
        if 'id' in request.POST:
            id = request.POST.get('id', '')
            try:
                id = int(id)
            except:
                raise Http404()
            target = Target.objects.get(id=id)
            target.state = "9"
            target.save()

            return HttpResponse(1)
        else:
            return HttpResponse(0)


def target_app_index(request, funid):
    """
    指标管理
    """
    if request.user.is_authenticated():
        operation_type_list = []
        cycle_type_list = []
        business_type_list = []
        unit_list = []
        source_list = []
        cycle_list = []
        storage_list = []
        app_list = []
        adminapp = ""
        try:
            cur_fun = Fun.objects.filter(id=int(funid)).exclude(state='9')
            adminapp = cur_fun[0].app
        except:
            return HttpResponseRedirect("/index")

        applist = App.objects.all().exclude(state='9')
        for i in applist:
            app_list.append({
                "app_name": i.name,
                "app_id": i.id,
            })

        c_dict_index_1 = DictIndex.objects.filter(
            id=1).exclude(state='9')
        if c_dict_index_1.exists():
            c_dict_index_1 = c_dict_index_1[0]
            dict_list1 = c_dict_index_1.dictlist_set.exclude(state="9")
            for i in dict_list1:
                operation_type_list.append({
                    "operation_type_name": i.name,
                    "operation_type_id": i.id,
                })

        c_dict_index_2 = DictIndex.objects.filter(
            id=12).exclude(state='9')
        if c_dict_index_2.exists():
            c_dict_index_2 = c_dict_index_2[0]
            dict_list2 = c_dict_index_2.dictlist_set.exclude(state="9")
            for i in dict_list2:
                cycle_type_list.append({
                    "cycle_type_name": i.name,
                    "cycle_type_id": i.id,
                })

        c_dict_index_3 = DictIndex.objects.filter(
            id=5).exclude(state='9')
        if c_dict_index_3.exists():
            c_dict_index_3 = c_dict_index_3[0]
            dict_list3 = c_dict_index_3.dictlist_set.exclude(state="9")
            for i in dict_list3:
                business_type_list.append({
                    "business_type_name": i.name,
                    "business_type_id": i.id,
                })

        c_dict_index_4 = DictIndex.objects.filter(
            id=6).exclude(state='9')
        if c_dict_index_4.exists():
            c_dict_index_4 = c_dict_index_4[0]
            dict_list4 = c_dict_index_4.dictlist_set.exclude(state="9")
            for i in dict_list4:
                unit_list.append({
                    "unit_name": i.name,
                    "unit_id": i.id,
                })

        sourcelist = Source.objects.all().exclude(state='9').exclude(pnode_id=None).filter(type='')
        for i in sourcelist:
            source_list.append({
                "source_name": i.name,
                "source_id": i.id,
            })

        cyclelist = Cycle.objects.all().exclude(state='9')
        for i in cyclelist:
            cycle_list.append({
                "cycle_name": i.name,
                "cycle_id": i.id,
            })

        all_dict_list = DictList.objects.exclude(state='9').values('id', 'name')

        storagelist = Storage.objects.all().exclude(state='9')
        for i in storagelist:
            storage_type = i.storagetype
            storage_type_display = ""
            for dict in all_dict_list:
                if storage_type == str(dict['id']):
                    storage_type_display = dict['name']
                    break
            storage_list.append({
                "storage_name": i.name,
                "storage_id": i.id,
                "storage_type": storage_type_display,
                "tablename": i.tablename,
            })

        # 所有业务
        works_list = []
        if adminapp:
            works_list = adminapp.work_set.exclude(state='9').values('id', 'name', 'core')

        return render(request, 'target_app.html',
                      {'username': request.user.userinfo.fullname,
                       "app_list": app_list,
                       "operation_type_list": operation_type_list,
                       "cycle_type_list": cycle_type_list,
                       "business_type_list": business_type_list,
                       "unit_list": unit_list,
                       "source_list": source_list,
                       "cycle_list": cycle_list,
                       "storage_list": storage_list,
                       "adminapp": adminapp.id if adminapp else '',
                       "works_list": works_list,
                       "pagefuns": getpagefuns(funid)})
    else:
        return HttpResponseRedirect("/login")


def target_importadminapp(request):
    if request.user.is_authenticated():
        adminapp = request.POST.get("adminapp", "")
        selectedtarget = request.POST.get('selectedtarget', '[]')

        result = {}
        try:
            app_id = int(adminapp)
        except:
            result["res"] = '数据异常，请重新打开页面。'
        else:
            my_app = App.objects.exclude(state="9").filter(id=app_id)
            if len(my_app) > 0:
                curapp = my_app[0]

                Target.objects.exclude(state="9").filter(
                    id__in=[int(target) for target in eval(selectedtarget)]).update(**{
                    'adminapp': curapp
                })

                result["res"] = '导入完成。'
            else:
                result["res"] = '当前应用不存在。'

        return JsonResponse(result)


def target_app_search_index(request, funid):
    """
    指标管理
    """
    if request.user.is_authenticated():
        operation_type_list = []
        cycle_type_list = []
        business_type_list = []
        unit_list = []
        source_list = []
        cycle_list = []
        storage_list = []
        adminapp = ""
        try:
            cur_fun = Fun.objects.filter(id=int(funid)).exclude(state='9')
            adminapp = cur_fun[0].app_id
        except:
            return HttpResponseRedirect("/index")

        c_dict_index_1 = DictIndex.objects.filter(
            id=1).exclude(state='9')
        if c_dict_index_1.exists():
            c_dict_index_1 = c_dict_index_1[0]
            dict_list1 = c_dict_index_1.dictlist_set.exclude(state="9")
            for i in dict_list1:
                operation_type_list.append({
                    "operation_type_name": i.name,
                    "operation_type_id": i.id,
                })

        c_dict_index_2 = DictIndex.objects.filter(
            id=12).exclude(state='9')
        if c_dict_index_2.exists():
            c_dict_index_2 = c_dict_index_2[0]
            dict_list2 = c_dict_index_2.dictlist_set.exclude(state="9")
            for i in dict_list2:
                cycle_type_list.append({
                    "cycle_type_name": i.name,
                    "cycle_type_id": i.id,
                })

        c_dict_index_3 = DictIndex.objects.filter(
            id=5).exclude(state='9')
        if c_dict_index_3.exists():
            c_dict_index_3 = c_dict_index_3[0]
            dict_list3 = c_dict_index_3.dictlist_set.exclude(state="9")
            for i in dict_list3:
                business_type_list.append({
                    "business_type_name": i.name,
                    "business_type_id": i.id,
                })

        c_dict_index_4 = DictIndex.objects.filter(
            id=6).exclude(state='9')
        if c_dict_index_4.exists():
            c_dict_index_4 = c_dict_index_4[0]
            dict_list4 = c_dict_index_4.dictlist_set.exclude(state="9")
            for i in dict_list4:
                unit_list.append({
                    "unit_name": i.name,
                    "unit_id": i.id,
                })

        sourcelist = Source.objects.all().exclude(state='9').filter(type='')
        for i in sourcelist:
            source_list.append({
                "source_name": i.name,
                "source_id": i.id,
            })

        cyclelist = Cycle.objects.all().exclude(state='9')
        for i in cyclelist:
            cycle_list.append({
                "cycle_name": i.name,
                "cycle_id": i.id,
            })

        storagelist = Storage.objects.all().exclude(state='9')
        for i in storagelist:
            storage_list.append({
                "storage_name": i.name,
                "storage_id": i.id,
            })

        # 所有业务 所有应用
        all_works = Work.objects.exclude(state='9').values('app_id', 'id', 'name')
        all_apps = App.objects.exclude(state='9').values('id', 'name')
        search_app = []
        for aa in all_apps:
            works = []

            for aw in all_works:
                if aw['app_id'] == aa['id']:
                    works.append({
                        'id': aw['id'],
                        'name': aw['name']
                    })
            search_app.append({
                'id': aa['id'],
                'name': aa['name'],
                "works": works
            })

        return render(request, 'target_app_search.html',
                      {'username': request.user.userinfo.fullname,
                       "operation_type_list": operation_type_list,
                       "cycle_type_list": cycle_type_list,
                       "business_type_list": business_type_list,
                       "unit_list": unit_list,
                       "source_list": source_list,
                       "cycle_list": cycle_list,
                       "storage_list": storage_list,
                       "adminapp": adminapp,
                       "search_app": search_app,
                       "pagefuns": getpagefuns(funid)})
    else:
        return HttpResponseRedirect("/login")


def target_importapp(request):
    if request.user.is_authenticated():
        adminapp = request.POST.get("adminapp", "")
        selectedtarget = request.POST.get('selectedtarget', '[]')

        result = {}
        try:
            app_id = int(adminapp)
        except:
            result["res"] = '数据异常，请重新打开页面。'
        my_app = App.objects.exclude(state="9").filter(id=app_id)
        if len(my_app) > 0:
            curapp = my_app[0]
            for target in eval(selectedtarget):
                try:
                    my_target = Target.objects.exclude(state="9").get(id=int(target))
                    my_target.app.add(curapp)
                except Exception as e:
                    print(e)
            result["res"] = '导入完成。'
        else:
            result["res"] = '当前应用不存在。'

    return JsonResponse(result)


def target_app_del(request):
    if request.user.is_authenticated():
        if 'id' in request.POST:
            adminapp = request.POST.get("adminapp", "")
            id = request.POST.get('id', '')
            try:
                id = int(id)
                app_id = int(adminapp)
            except:
                raise Http404()
            my_app = App.objects.exclude(state="9").get(id=app_id)
            target = Target.objects.get(id=id)
            target.app.remove(my_app)
            target.save()

            return HttpResponse(1)
        else:
            return HttpResponse(0)


def constant_index(request, funid):
    if request.user.is_authenticated():
        app_list = []
        applist = App.objects.all().exclude(state='9')
        for i in applist:
            app_list.append({
                "app_name": i.name,
                "app_id": i.id,
            })

        return render(request, 'constant.html',
                      {'username': request.user.userinfo.fullname,
                       "app_list": app_list,
                       "pagefuns": getpagefuns(funid)})
    else:
        return HttpResponseRedirect("/login")


def constant_data(request):
    if request.user.is_authenticated():
        search_adminapp = request.GET.get('search_adminapp', '')
        result = []
        all_constant = Constant.objects.exclude(state="9").order_by("sort")
        if search_adminapp != "":
            if search_adminapp == 'null':
                all_constant = all_constant.filter(adminapp=None)
            else:
                curadminapp = App.objects.get(id=int(search_adminapp))
                all_constant = all_constant.filter(adminapp=curadminapp)

        for constant in all_constant:
            adminapp_name = ""
            try:
                adminapp_name = constant.adminapp.name
            except:
                pass
            value = "{:f}".format(decimal.Decimal(str(constant.value) if str(constant.value) else "0").normalize())
            result.append({
                "adminapp_name": adminapp_name,
                "id": constant.id,
                "name": constant.name,
                "unity": constant.unity,
                "code": constant.code,
                "value": value,
                "adminapp": constant.adminapp_id,
                "sort": constant.sort,
                "state": constant.state,
            })
        return JsonResponse({"data": result})


def constant_save(request):
    if request.user.is_authenticated():
        id = request.POST.get("id", "")
        name = request.POST.get("name", "")
        code = request.POST.get("code", "")
        value = request.POST.get("value", "")
        adminapp = request.POST.get("adminapp", "")
        sort = request.POST.get("sort", "")
        unity = request.POST.get("unity", "")

        all_app = App.objects.exclude(state="9")

        try:
            id = int(id)
        except:
            raise Http404()

        result = {}

        if name.strip() == '':
            result["res"] = '常数名称不能为空。'
        else:
            if code.strip() == '':
                result["res"] = '常数代码不能为空。'
            else:
                if value.strip() == '':
                    result["res"] = '常数值不能为空。'
                else:
                    if id == 0:
                        all_constant = Constant.objects.filter(code=code).exclude(state="9")
                        all_target = Target.objects.filter(code=code).exclude(state="9")
                        if (len(all_constant) > 0):
                            result["res"] = '常数代码:' + code + '已存在。'
                        else:
                            if (len(all_target) > 0):
                                result["res"] = '指标库内已存在:' + code + '。'
                            else:
                                constant_save = Constant()
                                constant_save.name = name
                                constant_save.code = code
                                constant_save.value = float(value)
                                constant_save.unity = unity

                                try:
                                    app_id = int(adminapp)
                                    my_app = all_app.get(id=app_id)
                                    constant_save.adminapp = my_app
                                except:
                                    pass
                                try:
                                    constant_save.sort = int(sort)
                                except:
                                    pass
                                constant_save.save()
                                result["res"] = "保存成功。"
                                result["data"] = constant_save.id

                    else:
                        all_constant = Constant.objects.filter(code=code).exclude(id=id).exclude(state="9")
                        all_target = Target.objects.filter(code=code).exclude(state="9")
                        if (len(all_constant) > 0):
                            result["res"] = '常数代码:' + code + '已存在。'
                        else:
                            if (len(all_target) > 0):
                                result["res"] = '指标库内已存在:' + code + '。'
                            else:
                                try:
                                    constant_save = Constant.objects.get(id=id)
                                    constant_save.name = name
                                    constant_save.code = code
                                    constant_save.value = float(value)
                                    constant_save.unity = unity

                                    try:
                                        app_id = int(adminapp)
                                        my_app = all_app.get(id=app_id)
                                        constant_save.adminapp = my_app
                                    except:
                                        pass
                                    try:
                                        constant_save.sort = int(sort)
                                    except:
                                        pass

                                    constant_save.save()
                                    result["res"] = "保存成功。"
                                    result["data"] = constant_save.id
                                except Exception as e:
                                    result["res"] = "修改失败。"

        return JsonResponse(result)


def constant_del(request):
    if request.user.is_authenticated():
        if 'id' in request.POST:
            id = request.POST.get('id', '')
            try:
                id = int(id)
            except:
                raise Http404()
            constant = Constant.objects.get(id=id)
            constant.state = "9"
            constant.save()
            return HttpResponse(1)
        else:
            return HttpResponse(0)


def constant_app_index(request, funid):
    if request.user.is_authenticated():
        try:
            cur_fun = Fun.objects.filter(id=int(funid)).exclude(state='9')
            adminapp = cur_fun[0].app
        except:
            return HttpResponseRedirect("/index")

        return render(request, 'constant_app.html',
                      {'username': request.user.userinfo.fullname,
                       "adminapp": adminapp.id if adminapp else '',
                       "pagefuns": getpagefuns(funid)})
    else:
        return HttpResponseRedirect("/login")


def getreporting_date(date, cycletype):
    if cycletype == "10":
        date = datetime.datetime.strptime(date, "%Y-%m-%d")
    if cycletype == "11":
        date = datetime.datetime.strptime(date, "%Y-%m")
        year = date.year
        month = date.month
        a, b = calendar.monthrange(year, month)  # a,b——weekday的第一天是星期几（0-6对应星期一到星期天）和这个月的所有天数
        date = datetime.datetime(year=year, month=month, day=b)  # 构造本月月末datetime
    if cycletype == "12":
        date = datetime.datetime.strptime(date, "%Y-%m-%d")
    if cycletype == "13":
        date = datetime.datetime.strptime(date, "%Y-%m-%d")

    if cycletype == "14":
        date = datetime.datetime.strptime(date, "%Y")
        date = date.replace(month=12, day=31)

    return date


def reporting_index(request, cycletype, funid):
    """
    数据填报
    """
    if request.user.is_authenticated():
        app = ""
        try:
            cur_fun = Fun.objects.filter(id=int(funid)).exclude(state='9')
            app = cur_fun[0].app_id
            work = cur_fun[0].work
        except:
            return HttpResponseRedirect("/index")
        else:
            now = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(
                days=-1)
            date = now.strftime("%Y-%m-%d")
            if cycletype == '10':
                now = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(
                    days=-1)
                date = now.strftime("%Y-%m-%d")
            if cycletype == '11':
                now = (datetime.datetime.now().replace(day=1, hour=0, minute=0, second=0,
                                                       microsecond=0) + datetime.timedelta(
                    days=-1))
                date = now.strftime("%Y-%m")
            seasondate = ''
            if cycletype == '12':
                now = datetime.datetime.now()
                month = (now.month - 1) - (now.month - 1) % 3 + 1
                now = (datetime.datetime.now().replace(month=month, day=1, hour=0, minute=0, second=0,
                                                       microsecond=0) + datetime.timedelta(
                    days=-1))
                year = now.strftime("%Y")
                if now.month in (1, 2, 3):
                    season = '第1季度'
                    seasondate = year + '-' + season
                    date = year + '-' + "03-31"
                if now.month in (4, 5, 6):
                    season = '第2季度'
                    seasondate = year + '-' + season
                    date = year + '-' + "06-30"
                if now.month in (7, 8, 9):
                    season = '第3季度'
                    seasondate = year + '-' + season
                    date = year + '-' + "09-30"
                if now.month in (10, 11, 12):
                    season = '第4季度'
                    seasondate = year + '-' + season
                    date = year + '-' + "12-31"
            yeardate = ''
            if cycletype == '13':
                now = datetime.datetime.now()
                month = (now.month - 1) - (now.month - 1) % 6 + 1
                now = (datetime.datetime.now().replace(month=month, day=1, hour=0, minute=0, second=0,
                                                       microsecond=0) + datetime.timedelta(
                    days=-1))
                year = now.strftime("%Y")
                if now.month in (1, 2, 3, 4, 5, 6):
                    season = '上半年'
                    yeardate = year + '-' + season
                    date = year + '-' + "06-30"
                if now.month in (7, 8, 9, 10, 11, 12):
                    season = '下半年'
                    yeardate = year + '-' + season
                    date = year + '-' + "12-31"
            if cycletype == '14':
                now = (datetime.datetime.now().replace(month=1, day=1, hour=0, minute=0, second=0,
                                                       microsecond=0) + datetime.timedelta(
                    days=-1))
                date = now.strftime("%Y")

            searchtag = ""
            metertag = ""
            entrytag = ""
            extracttag = ""
            calculatetag = ""

            searchtagclass = ""
            metertagclass = ""
            entrytagclass = ""
            extracttagclass = ""
            calculatetagclass = ""

            searchtagtabclass = ""
            metertagtabclass = ""
            entrytagtabclass = ""
            extracttagtabclass = ""
            calculatetagtabclass = ""

            meternew = ""
            entrynew = ""
            extractnew = ""
            calculatenew = ""

            meterreset = ""
            entryreset = ""
            extractreset = ""
            calculatereset = ""
            curapp = App.objects.filter(id=app)

            # 只有该功能对应的业务为核心业务，才显示数据查询标签
            if work is not None and work.core == '是':
                search_target = Target.objects.exclude(state='9').filter(cycletype=cycletype).filter(
                    (Q(app__in=curapp) & ~Q(adminapp__id=app)) | (Q(adminapp__id=app) & ~Q(work__core='是'))
                ).values(
                    'adminapp__id', 'adminapp__name', 'work_id'
                )
                works = Work.objects.exclude(state='9').values(
                    'id', 'name', 'app_id'
                )
            else:
                search_target = []
                works = []

            meter_target = Target.objects.exclude(state='9').filter(cycletype=cycletype, adminapp_id=app, work=work,
                                                                    operationtype='1')
            entry_target = Target.objects.exclude(state='9').filter(cycletype=cycletype, adminapp_id=app, work=work,
                                                                    operationtype='15')
            extract_target = Target.objects.exclude(state='9').filter(cycletype=cycletype, adminapp_id=app, work=work,
                                                                      operationtype='16')
            calculate_target = Target.objects.exclude(state='9').filter(cycletype=cycletype, adminapp_id=app, work=work,
                                                                        operationtype='17')

            meter_data = getmodels("Meterdata", str(now.year)).objects.exclude(state="9").filter(
                target__adminapp_id=app,
                target__cycletype=cycletype,
                target__work=work,
                datadate=now)
            entry_data = getmodels("Entrydata", str(now.year)).objects.exclude(state="9").filter(
                target__adminapp_id=app,
                target__cycletype=cycletype,
                target__work=work,
                datadate=now)
            extract_data = getmodels("Extractdata", str(now.year)).objects.exclude(state="9").filter(
                target__adminapp_id=app,
                target__work=work,
                target__cycletype=cycletype, datadate=now)
            calculate_data = getmodels("Calculatedata", str(now.year)).objects.exclude(state="9").filter(
                target__adminapp_id=app,
                target__work=work,
                target__cycletype=cycletype, datadate=now)
            search_app = []
            check_search_app = []

            if not search_target:
                searchtag = "display: none;"
            else:
                for target in search_target:
                    if target['adminapp__id']:
                        works_list = []
                        for w in works:
                            if target['adminapp__id'] == w['app_id'] and w['id'] != work.id:
                                # 过滤掉没有指标的业务项
                                has_target = False

                                for t in search_target:
                                    if t['work_id'] == w['id']:
                                        has_target = True
                                        break

                                if has_target:
                                    works_list.append({
                                        'id': w['id'],
                                        'name': w['name']
                                    })

                        # 数据查询的业务下拉框过滤掉没指标的项
                        cursearchapp = {
                            "id": target['adminapp__id'],
                            "name": target['adminapp__name'],
                            'works': works_list,
                        }
                        check_cursearchapp = {
                            "id": target['adminapp__id'],
                            "name": target['adminapp__name'],
                        }
                        if check_cursearchapp not in check_search_app:
                            search_app.append(cursearchapp)
                            check_search_app.append(check_cursearchapp)
            if len(meter_target) <= 0 and len(meter_data) <= 0:
                metertag = "display: none;"
            if len(entry_target) <= 0 and len(entry_data) <= 0:
                entrytag = "display: none;"
            if len(extract_target) <= 0 and len(extract_data) <= 0:
                extracttag = "display: none;"
            if len(calculate_target) <= 0 and len(calculate_data) <= 0:
                calculatetag = "display: none;"
            if len(meter_data) <= 0:
                meterreset = "display: none;"
            else:
                meternew = "display: none;"

            if search_target is not None and len(search_target) > 0:
                searchtagclass = "class=active"
                searchtagtabclass = "active in"
            elif len(meter_target) > 0:
                metertagclass = "class=active"
                metertagtabclass = "active in"
            elif len(entry_target) > 0:
                entrytagclass = "class=active"
                entrytagtabclass = "active in"
            elif len(extract_target) > 0:
                extracttagclass = "class=active"
                extracttagtabclass = "active in"
            elif len(calculate_target) > 0:
                calculatetagclass = "class=active"
                calculatetagtabclass = "active in"

            if len(entry_data) <= 0:
                entryreset = "display: none;"
            else:
                entrynew = "display: none;"
            if len(extract_data) <= 0:
                extractreset = "display: none;"
            else:
                extractnew = "display: none;"
            if len(calculate_data) <= 0:
                calculatereset = "display: none;"
            else:
                calculatenew = "display: none;"

            return render(request, 'reporting.html',
                          {'username': request.user.userinfo.fullname,
                           "cycletype": cycletype,
                           "app": app,
                           "date": date,
                           "seasondate": seasondate,
                           "yeardate": yeardate,
                           "searchtag": searchtag,
                           "metertag": metertag,
                           "entrytag": entrytag,
                           "extracttag": extracttag,
                           "calculatetag": calculatetag,
                           "searchtagclass": searchtagclass,
                           "metertagclass": metertagclass,
                           "entrytagclass": entrytagclass,
                           "extracttagclass": extracttagclass,
                           "calculatetagclass": calculatetagclass,
                           "searchtagtabclass": searchtagtabclass,
                           "metertagtabclass": metertagtabclass,
                           "entrytagtabclass": entrytagtabclass,
                           "extracttagtabclass": extracttagtabclass,
                           "calculatetagtabclass": calculatetagtabclass,
                           "meternew": meternew,
                           "entrynew": entrynew,
                           "extractnew": extractnew,
                           "calculatenew": calculatenew,
                           "meterreset": meterreset,
                           "entryreset": entryreset,
                           "extractreset": extractreset,
                           "calculatereset": calculatereset,
                           "search_app": search_app,
                           "pagefuns": getpagefuns(funid),
                           "funid": funid})
    else:
        return HttpResponseRedirect("/login")


def reporting_data(request):
    if request.user.is_authenticated():

        result = []
        app = request.GET.get('app', '')
        cycletype = request.GET.get('cycletype', '')
        reporting_date = request.GET.get('reporting_date', '')
        operationtype = request.GET.get('operationtype', '')
        funid = request.GET.get('funid', '')
        try:
            app = int(app)
            reporting_date = getreporting_date(reporting_date, cycletype)
        except:
            raise Http404()
        all_data = []
        work = None
        try:
            funid = int(funid)
            fun = Fun.objects.get(id=funid)
            work = fun.work
        except:
            pass
        else:
            if operationtype == "1":
                all_data = getmodels("Meterdata", str(reporting_date.year)).objects.exclude(state="9").filter(
                    target__adminapp_id=app, target__cycletype=cycletype, datadate=reporting_date,
                    target__work=work).order_by("target__sort").select_related("target")
            if operationtype == "15":
                all_data = getmodels("Entrydata", str(reporting_date.year)).objects.exclude(state="9").filter(
                    target__adminapp_id=app, target__cycletype=cycletype, datadate=reporting_date,
                    target__work=work).order_by("target__sort").select_related("target")
            if operationtype == "16":
                all_data = getmodels("Extractdata", str(reporting_date.year)).objects.exclude(state="9").filter(
                    target__adminapp_id=app, target__cycletype=cycletype, datadate=reporting_date,
                    target__work=work).order_by("target__sort").select_related("target")
            if operationtype == "17":
                all_data = getmodels("Calculatedata", str(reporting_date.year)).objects.exclude(state="9").filter(
                    target__adminapp_id=app, target__cycletype=cycletype, datadate=reporting_date,
                    target__work=work).order_by("target__sort").select_related("target")

            all_dict_list = DictList.objects.exclude(state='9').values('id', 'name')

            # 电表走字数据
            all_changedata = Meterchangedata.objects.exclude(state="9").filter(datadate=reporting_date).values()

            for data in all_data:
                businesstypename = data.target.businesstype

                try:
                    if businesstypename:
                        for dict in all_dict_list:
                            if businesstypename == str(dict['id']):
                                businesstypename = dict['name']
                                break
                except:
                    pass
                unitname = data.target.unit
                try:
                    if unitname:
                        for dict in all_dict_list:
                            if unitname == str(dict['id']):
                                unitname = dict['name']
                                break
                except:
                    pass
                curvalue = ""
                curvaluedate = ""
                cumulativemonth = ""
                cumulativequarter = ""
                cumulativehalfyear = ""
                cumulativeyear = ""
                try:
                    curvalue = round(data.curvalue, data.target.digit)
                except:
                    pass
                try:
                    curvaluedate = data.curvaluedate.strftime('%Y-%m-%d %H:%M:%S') if data.curvaluedate else "",
                except:
                    pass
                if data.target.cumulative in ['1', '2', '3', '4']:
                    try:
                        cumulativemonth = round(data.cumulativemonth, data.target.digit)
                    except:
                        pass
                    try:
                        cumulativequarter = round(data.cumulativequarter, data.target.digit)
                    except:
                        pass
                    try:
                        cumulativehalfyear = round(data.cumulativehalfyear, data.target.digit)
                    except:
                        pass
                    try:
                        cumulativeyear = round(data.cumulativeyear, data.target.digit)
                    except:
                        pass
                if operationtype in ("15", "16", "17"):
                    result.append({
                        "id": data.id,
                        "curvalue": curvalue,
                        "curvaluedate": curvaluedate,
                        "curvaluetext": data.curvaluetext if data.curvaluetext else '',
                        "cumulativemonth": cumulativemonth,
                        "cumulativequarter": cumulativequarter,
                        "cumulativehalfyear": cumulativehalfyear,
                        "cumulativeyear": cumulativeyear,
                        "releasestate": data.releasestate,
                        "target_id": data.target.id,
                        "target_name": data.target.name,
                        "target_unity": data.target.unity,
                        "target_code": data.target.code,
                        "target_businesstype": data.target.businesstype,
                        "target_unit": data.target.unit,
                        "target_businesstypename": businesstypename,
                        "target_unitname": unitname,
                        "target_datatype": data.target.datatype,
                        "target_cumulative": data.target.cumulative,
                        "target_magnification": data.target.magnification,
                        "target_upperlimit": data.target.upperlimit,
                        "target_lowerlimit": data.target.lowerlimit,
                    })
                elif operationtype == "1":
                    zerodata = "{:f}".format(decimal.Decimal(data.zerodata if data.zerodata else "0").normalize())
                    twentyfourdata = "{:f}".format(
                        decimal.Decimal(data.twentyfourdata if data.zerodata else "0").normalize())
                    metervalue = data.metervalue
                    meterchangedata_id = ""
                    oldtable_zerodata = ""
                    oldtable_twentyfourdata = ""
                    oldtable_value = ""
                    oldtable_magnification = ""
                    oldtable_finalvalue = ""
                    newtable_zerodata = ""
                    newtable_twentyfourdata = ""
                    newtable_value = ""
                    newtable_magnification = ""
                    newtable_finalvalue = ""
                    finalvalue = ""

                    cur_meterchange = {}
                    for mcd in all_changedata:
                        if mcd['meterdata'] == data.id:
                            cur_meterchange = mcd
                            break

                    if cur_meterchange:
                        meterchangedata_id = cur_meterchange['id']
                        oldtable_zerodata = cur_meterchange['oldtable_zerodata']
                        oldtable_twentyfourdata = cur_meterchange['oldtable_twentyfourdata']
                        oldtable_value = cur_meterchange['oldtable_value']
                        oldtable_magnification = cur_meterchange['oldtable_magnification']
                        oldtable_finalvalue = cur_meterchange['oldtable_finalvalue']
                        newtable_zerodata = cur_meterchange['newtable_zerodata']
                        newtable_twentyfourdata = cur_meterchange['newtable_twentyfourdata']
                        newtable_value = cur_meterchange['newtable_value']
                        newtable_magnification = cur_meterchange['newtable_magnification']
                        newtable_finalvalue = cur_meterchange['newtable_finalvalue']
                        finalvalue = cur_meterchange['finalvalue']
                        if data.target.cumulative in ['1', '2', '3', '4']:
                            try:
                                oldtable_zerodata = round(oldtable_zerodata, data.target.digit)
                            except:
                                pass
                            try:
                                oldtable_twentyfourdata = round(oldtable_twentyfourdata, data.target.digit)
                            except:
                                pass
                            try:
                                oldtable_value = round(oldtable_value, data.target.digit)
                            except:
                                pass
                            try:
                                oldtable_magnification = round(oldtable_magnification, data.target.digit)
                            except:
                                pass
                            try:
                                oldtable_finalvalue = round(oldtable_finalvalue, data.target.digit)
                            except:
                                pass
                            try:
                                newtable_zerodata = round(newtable_zerodata, data.target.digit)
                            except:
                                pass
                            try:
                                newtable_twentyfourdata = round(newtable_twentyfourdata, data.target.digit)
                            except:
                                pass
                            try:
                                newtable_value = round(newtable_value, data.target.digit)
                            except:
                                pass
                            try:
                                newtable_magnification = round(newtable_magnification, data.target.digit)
                            except:
                                pass
                            try:
                                newtable_finalvalue = round(newtable_finalvalue, data.target.digit)
                            except:
                                pass
                            try:
                                finalvalue = round(finalvalue, data.target.digit)
                            except:
                                pass

                    result.append({
                        "id": data.id,
                        "curvalue": curvalue,
                        "curvaluedate": curvaluedate,
                        "curvaluetext": data.curvaluetext,
                        "cumulativemonth": cumulativemonth,
                        "cumulativequarter": cumulativequarter,
                        "cumulativehalfyear": cumulativehalfyear,
                        "cumulativeyear": cumulativeyear,
                        "releasestate": data.releasestate,
                        "target_id": data.target.id,
                        "target_name": data.target.name,
                        "target_unity": data.target.unity,
                        "target_code": data.target.code,
                        "target_businesstype": data.target.businesstype,
                        "target_unit": data.target.unit,
                        "target_businesstypename": businesstypename,
                        "target_unitname": unitname,
                        "target_datatype": data.target.datatype,
                        "target_cumulative": data.target.cumulative,
                        "target_magnification": data.target.magnification,
                        "target_upperlimit": data.target.upperlimit,
                        "target_lowerlimit": data.target.lowerlimit,

                        "zerodata": zerodata,
                        "twentyfourdata": twentyfourdata,
                        "metervalue": metervalue,
                        "meterchangedata_id": meterchangedata_id,
                        "oldtable_zerodata": oldtable_zerodata,
                        "oldtable_twentyfourdata": oldtable_twentyfourdata,
                        "oldtable_value": oldtable_value,
                        "oldtable_magnification": oldtable_magnification,
                        "oldtable_finalvalue": oldtable_finalvalue,
                        "newtable_zerodata": newtable_zerodata,
                        "newtable_twentyfourdata": newtable_twentyfourdata,
                        "newtable_value": newtable_value,
                        "newtable_magnification": newtable_magnification,
                        "newtable_finalvalue": newtable_finalvalue,
                        "finalvalue": finalvalue,

                    })
        return JsonResponse({"data": result})


def reporting_search_data(request):
    if request.user.is_authenticated():

        result = []
        app = request.GET.get('app', '')
        cycletype = request.GET.get('cycletype', '')
        reporting_date = request.GET.get('reporting_date', '')
        searchapp = request.GET.get('searchapp', '')
        works = request.GET.get('works', '')

        try:
            app = int(app)
            reporting_date = getreporting_date(reporting_date, cycletype)
        except:
            raise Http404()
        all_data = []

        # 查询的内容目前为非本应用的有查询权限的查询指标，应该再加上本应用内的非核心业务的指标
        # >> 除本应用核心业务之外的所有指标
        except_works = Work.objects.exclude(state='9').filter(app_id=app, core='是')

        curapp = App.objects.get(id=app)
        all_target = Target.objects.exclude(state="9").exclude(work__in=except_works). \
            filter(cycletype=cycletype).filter(Q(app=curapp) | Q(adminapp=curapp)).order_by("adminapp", "operationtype",
                                                                                            "sort")

        if searchapp != "":
            try:
                cursearchapp = App.objects.get(id=int(searchapp))
                all_target = all_target.filter(adminapp=cursearchapp)
            except:
                pass

        if works != "":
            try:
                works = int(works)
                all_target = all_target.filter(work_id=works)
            except Exception as e:
                print(e)

        for target in all_target:
            curtargetdata = {"target": target, "zerodata": "", "twentyfourdata": "", "metervalue": "", "curvalue": "",
                             "curvaluedate": "", "curvaluetext": "", "cumulativemonth": "", "cumulativequarter": "",
                             "cumulativehalfyear": "", "cumulativeyear": "", "releasestate": ""}
            if target.operationtype == "15":
                targetvalue = getmodels("Entrydata", str(reporting_date.year)).objects.exclude(state="9").filter(
                    target=target, datadate=reporting_date)
                if len(targetvalue) > 0:
                    curtargetdata = {"target": target, "zerodata": "", "twentyfourdata": "", "metervalue": "",
                                     "curvalue": targetvalue[0].curvalue, "curvaluedate": targetvalue[0].curvaluedate,
                                     "curvaluetext": targetvalue[0].curvaluetext,
                                     "cumulativemonth": targetvalue[0].cumulativemonth,
                                     "cumulativequarter": targetvalue[0].cumulativequarter,
                                     "cumulativehalfyear": targetvalue[0].cumulativehalfyear,
                                     "cumulativeyear": targetvalue[0].cumulativeyear,
                                     "releasestate": targetvalue[0].releasestate}
            elif target.operationtype == "16":
                targetvalue = getmodels("Extractdata", str(reporting_date.year)).objects.exclude(state="9").filter(
                    target=target, datadate=reporting_date)
                if len(targetvalue) > 0:
                    curtargetdata = {"target": target, "zerodata": "", "twentyfourdata": "", "metervalue": "",
                                     "curvalue": targetvalue[0].curvalue, "curvaluedate": targetvalue[0].curvaluedate,
                                     "curvaluetext": targetvalue[0].curvaluetext,
                                     "cumulativemonth": targetvalue[0].cumulativemonth,
                                     "cumulativequarter": targetvalue[0].cumulativequarter,
                                     "cumulativehalfyear": targetvalue[0].cumulativehalfyear,
                                     "cumulativeyear": targetvalue[0].cumulativeyear,
                                     "releasestate": targetvalue[0].releasestate}
            elif target.operationtype == "17":
                targetvalue = getmodels("Calculatedata", str(reporting_date.year)).objects.exclude(state="9").filter(
                    target=target, datadate=reporting_date)
                if len(targetvalue) > 0:
                    curtargetdata = {"target": target, "zerodata": "", "twentyfourdata": "", "metervalue": "",
                                     "curvalue": targetvalue[0].curvalue, "curvaluedate": targetvalue[0].curvaluedate,
                                     "curvaluetext": targetvalue[0].curvaluetext,
                                     "cumulativemonth": targetvalue[0].cumulativemonth,
                                     "cumulativequarter": targetvalue[0].cumulativequarter,
                                     "cumulativehalfyear": targetvalue[0].cumulativehalfyear,
                                     "cumulativeyear": targetvalue[0].cumulativeyear,
                                     "releasestate": targetvalue[0].releasestate}
            elif target.operationtype == "1":
                targetvalue = getmodels("Meterdata", str(reporting_date.year)).objects.exclude(state="9").filter(
                    target=target, datadate=reporting_date)
                if len(targetvalue) > 0:
                    curtargetdata = {"target": target, "zerodata": targetvalue[0].zerodata,
                                     "twentyfourdata": targetvalue[0].twentyfourdata,
                                     "metervalue": targetvalue[0].metervalue, "curvalue": targetvalue[0].curvalue,
                                     "curvaluedate": targetvalue[0].curvaluedate,
                                     "curvaluetext": targetvalue[0].curvaluetext,
                                     "cumulativemonth": targetvalue[0].cumulativemonth,
                                     "cumulativequarter": targetvalue[0].cumulativequarter,
                                     "cumulativehalfyear": targetvalue[0].cumulativehalfyear,
                                     "cumulativeyear": targetvalue[0].cumulativeyear,
                                     "releasestate": targetvalue[0].releasestate}
            all_data.append(curtargetdata)

        all_dict_list = DictList.objects.exclude(state='9').values('id', 'name')

        for data in all_data:
            businesstypename = data["target"].businesstype

            try:
                if businesstypename:
                    for dict in all_dict_list:
                        if businesstypename == str(dict['id']):
                            businesstypename = dict['name']
                            break
            except:
                pass
            unitname = data["target"].unit
            try:
                if unitname:
                    for dict in all_dict_list:
                        if unitname == str(dict['id']):
                            unitname = dict['name']
                            break
            except:
                pass
            cumulativemonth = ""
            cumulativequarter = ""
            cumulativehalfyear = ""
            cumulativeyear = ""
            curvalue = ""
            if data["target"].datatype == "numbervalue":
                curvalue = data["curvalue"]
                try:
                    curvalue = round(data["curvalue"], data["target"].digit)
                except:
                    pass
            elif data["target"].datatype == "date":
                curvalue = ""
                try:
                    curvalue = data["curvaluedate"].strftime('%Y-%m-%d %H:%M:%S') if data["curvaluedate"] else ""
                except:
                    pass
            elif data["target"].datatype == "text":
                curvalue = data["curvaluetext"]
            if data["target"].cumulative in ['1', '2', '3', '4']:
                try:
                    cumulativemonth = round(data["cumulativemonth"], data["target"].digit)
                except:
                    pass
                try:
                    cumulativequarter = round(data["cumulativequarter"], data["target"].digit)
                except:
                    pass
                try:
                    cumulativehalfyear = round(data["cumulativehalfyear"], data["target"].digit)
                except:
                    pass
                try:
                    cumulativeyear = round(data["cumulativeyear"], data["target"].digit)
                except:
                    pass
            result.append({
                "curvalue": curvalue,
                "cumulativemonth": cumulativemonth,
                "cumulativequarter": cumulativequarter,
                "cumulativehalfyear": cumulativehalfyear,
                "cumulativeyear": cumulativeyear,
                "target_id": data["target"].id,
                "target_name": data["target"].name,
                "target_unity": data["target"].unity,
                "target_code": data["target"].code,
                "target_businesstype": data["target"].businesstype,
                "target_unit": data["target"].unit,
                "target_businesstypename": businesstypename,
                "target_unitname": unitname,
                "target_datatype": data["target"].datatype,
                "target_cumulative": data["target"].cumulative,
                "target_magnification": data["target"].magnification,
                "target_upperlimit": data["target"].upperlimit,
                "target_lowerlimit": data["target"].lowerlimit,

                "zerodata": data["zerodata"],
                "twentyfourdata": data["twentyfourdata"],
                "metervalue": data["metervalue"],
                "releasestate": data["releasestate"]
            })
        return JsonResponse({"data": result})


def getcumulative(tableList, target, date, value):
    """
    数据累计
        求和
        算术平均
        加权平均
    """
    cumulativemonth = value
    cumulativequarter = value
    cumulativehalfyear = value
    cumulativeyear = value

    def get_last_cumulative_data(tableList, tmp_target, tmp_date):
        """
        找到指标指点时间点的月累计值、季累计值、半年累计值、年累计值
        :param tableList:
        :param tmp_target:
        :param tmp_date:
        :return:
        """
        lastcumulativemonth = 0
        lastcumulativequarter = 0
        lastcumulativehalfyear = 0
        lastcumulativeyear = 0

        lastg_date = datetime.datetime.strptime('2000-01-01', "%Y-%m-%d")
        # 周期类型 =>
        #   昨日
        #   上个月末
        #   上个季度末
        #   上个半年末
        #   上个年末
        if tmp_target.cycletype == "10":
            lastg_date = tmp_date + datetime.timedelta(days=-1)
        if tmp_target.cycletype == "11":
            lastg_date = tmp_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(
                days=-1)
        if tmp_target.cycletype == "12":
            month = (tmp_date.month - 1) - (tmp_date.month - 1) % 3 + 1  # 10
            newdate = datetime.datetime(tmp_date.year, month, 1)
            lastg_date = newdate + datetime.timedelta(days=-1)
        if tmp_target.cycletype == "13":
            month = (tmp_date.month - 1) - (tmp_date.month - 1) % 6 + 1  # 10
            newdate = datetime.datetime(tmp_date.year, month, 1)
            lastg_date = newdate + datetime.timedelta(days=-1)
        if tmp_target.cycletype == "14":
            lastg_date = tmp_date.replace(
                month=1, day=1, hour=0, minute=0, second=0, microsecond=0
            ) + datetime.timedelta(days=-1)

        queryset = tableList["Entrydata"].objects
        operationtype = tmp_target.operationtype
        if operationtype == "1":
            queryset = tableList["Meterdata"].objects
        if operationtype == "15":
            queryset = tableList["Entrydata"].objects
        if operationtype == "16":
            queryset = tableList["Extractdata"].objects
        if operationtype == "17":
            queryset = tableList["Calculatedata"].objects

        all_data = queryset.exclude(state="9").filter(target=tmp_target, datadate=lastg_date)
        if len(all_data) > 0:
            try:
                if lastg_date.year == tmp_date.year and lastg_date.month == tmp_date.month:
                    lastcumulativemonth += all_data[0].cumulativemonth
            except:
                pass
            try:
                if lastg_date.year == tmp_date.year and (lastg_date.month - 1) - (lastg_date.month - 1) % 3 == (
                        tmp_date.month - 1) - (tmp_date.month - 1) % 3:
                    lastcumulativequarter += all_data[0].cumulativequarter
            except:
                pass
            try:
                if lastg_date.year == tmp_date.year and (lastg_date.month - 1) - (lastg_date.month - 1) % 6 == (
                        tmp_date.month - 1) - (tmp_date.month - 1) % 6:
                    lastcumulativehalfyear += all_data[0].cumulativehalfyear
            except:
                pass
            try:
                if lastg_date.year == tmp_date.year:
                    lastcumulativeyear += all_data[0].cumulativeyear
            except:
                pass

        return lastcumulativemonth, lastcumulativequarter, lastcumulativehalfyear, lastcumulativeyear

    lastcumulativemonth, lastcumulativequarter, lastcumulativehalfyear, lastcumulativeyear \
        = get_last_cumulative_data(tableList, target, date)

    cumulative = target.cumulative
    weight_target = target.weight_target

    if cumulative == '1':  # 求和
        cumulativemonth = lastcumulativemonth + value
        cumulativequarter = lastcumulativequarter + value
        cumulativehalfyear = lastcumulativehalfyear + value
        cumulativeyear = lastcumulativeyear + value
    if cumulative == '2':  # 算术平均，保留位数
        if target.cycletype == "10":
            # 日报
            yestoday_date = date + datetime.timedelta(days=-1)
            if date.year == yestoday_date.year:
                # 当月昨天天数、当季到昨天的天数、半年到昨天的天数、当年到昨天的天数
                def get_days(start_time, end_time):
                    return int(
                        (end_time.replace(hour=0, minute=0, second=0, microsecond=0) - start_time.replace(
                            day=1, hour=0, minute=0, second=0, microsecond=0
                        )).total_seconds() / (60 * 60 * 24)
                    ) + 1

                now = datetime.datetime.now()

                # 1.当月昨天的天数
                if date.day > 1:  # 日报月初月累计为当前值
                    cumulativemonth = ((lastcumulativemonth * (date.day - 1)) + value) / date.day
                # 2.当季到昨天的天数
                # 判断当前月所在季度，第一季度/非第一季度
                if date.month <= 3:
                    days_in_quarter = get_days(now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
                                               yestoday_date)
                    cumulativequarter = (lastcumulativequarter * days_in_quarter + value) / (days_in_quarter + 1)
                else:
                    # 判断是否所在季度第一天
                    if not (date.month % 3 == 1 and date.day == 1):
                        # 当季到昨天的天数 = 昨天天数 - 上季度末天数
                        m_month = (date.month - 1) - (date.month - 1) % 3 + 1  # 10
                        m_newdate = datetime.datetime(date.year, m_month, 1)
                        days_in_quarter = get_days(
                            m_newdate.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
                            yestoday_date)
                        cumulativequarter = (lastcumulativequarter * days_in_quarter + value) / (days_in_quarter + 1)
                # 3.半年到昨天的天数(区分前/后半年)
                if date.month - 6 < 0:
                    days_in_halfyear = get_days(now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
                                                yestoday_date)
                    cumulativehalfyear = (lastcumulativehalfyear * days_in_halfyear + value) / (days_in_halfyear + 1)
                else:
                    # 判断是否后半年的第一天
                    if not (date.month == 7 and date.day == 1):
                        # 半年到昨天的天数 = 昨天天数 - 上半年末天数
                        h_month = (date.month - 1) - (date.month - 1) % 6 + 1  # 10
                        h_newdate = datetime.datetime(date.year, h_month, 1)
                        days_in_halfyear = get_days(
                            h_newdate.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
                            yestoday_date)
                        cumulativehalfyear = (lastcumulativehalfyear * days_in_halfyear + value) / (
                                days_in_halfyear + 1)
                # 4.当年到昨天的天数
                days_in_year = get_days(now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
                                        yestoday_date)
                cumulativeyear = (lastcumulativeyear * days_in_year + value) / days_in_year + 1
            else:
                pass
        if target.cycletype == "11":
            # 月报
            if date.month > 1:
                last_month_date = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0) + \
                                  datetime.timedelta(days=-1)
                # 1.上个月份
                # last_months = last_month_date.month
                # cumulativemonth = (lastcumulativemonth * last_months + value) / (last_months + 1)
                # 2.当季上个月所在月份
                if date.month > 3:  # 不是第一个季度
                    last_month_on_quarter = last_month_date.month % 3
                else:
                    last_month_on_quarter = last_month_date.month
                if last_month_on_quarter > 0:  # 任何一季度首月季累计为当前值
                    cumulativequarter = (lastcumulativequarter * last_month_on_quarter + value) / (
                            last_month_on_quarter + 1)
                # 3.半年上个月所在月份(区分前/后半年)
                last_month_on_halfyear = -1
                if date.month > 6:
                    if date.month - 6 > 1:
                        last_month_on_halfyear = last_month_date.month - 6
                else:
                    last_month_on_halfyear = last_month_date.month
                if last_month_on_halfyear != -1:
                    cumulativehalfyear = (lastcumulativehalfyear * last_month_on_halfyear + value) / (
                            last_month_on_halfyear + 1)
                # 4.年上个月所在月份
                last_month_on_year = last_month_date.month
                cumulativeyear = (lastcumulativeyear * last_month_on_year + value) / (last_month_on_year + 1)
            else:
                pass
        if target.cycletype == "12":
            # 季报
            if date.month > 3:  # 非第一季度
                q_month = (date.month - 1) - (date.month - 1) % 3 + 1  # 10
                q_newdate = datetime.datetime(date.year, q_month, 1)
                last_quarter_date = q_newdate + datetime.timedelta(days=-1)

                # 1.上个季度
                last_quarters = last_quarter_date.month // 3
                cumulativequarter = (lastcumulativequarter * last_quarters + value) / (last_quarters + 1)
                # 2.半年所在季度(区分前/后半年)
                if date.month in [4, 5, 6, 10, 11, 12]:
                    quarter_on_halfyear = 1
                    cumulativehalfyear = (lastcumulativehalfyear * quarter_on_halfyear + value) / (
                            quarter_on_halfyear + 1)
                # 3.年所在季度
                quarter_on_year = last_quarter_date.month // 3
                cumulativeyear = (lastcumulativeyear * quarter_on_year + value) / (quarter_on_year + 1)
        if target.cycletype == "13":
            if date.month > 6:
                cumulativeyear = (lastcumulativeyear + value) / 2
        if target.cycletype == "14":
            # 年报均为当前值
            pass
    if cumulative == '3':  # 加权平均
        if not weight_target:
            raise Exception('未配置加权指标。')
        # 加权指标当前值
        wt_value = 0
        try:
            wt_target_id = target.weight_target_id
            queryset = tableList["Entrydata"].objects
            operationtype = target.operationtype
            if operationtype == "1":
                queryset = tableList["Meterdata"].objects
            if operationtype == "15":
                queryset = tableList["Entrydata"].objects
            if operationtype == "16":
                queryset = tableList["Extractdata"].objects
            if operationtype == "17":
                queryset = tableList["Calculatedata"].objects

            wt_calculatedata = queryset.exclude(state="9").filter(datadate=date).filter(target_id=wt_target_id)[0]
            wt_value = wt_calculatedata.curvalue
        except Exception as e:
            print(e)

        wt_lastcumulativemonth, wt_lastcumulativequarter, wt_lastcumulativehalfyear, wt_lastcumulativeyear \
            = get_last_cumulative_data(tableList, weight_target, date)
        if target.cycletype == "10":
            # 日报：
            yestoday_date = date + datetime.timedelta(days=-1)
            if date.year == yestoday_date.year:
                if date.day > 1:  # 日报月初月累计为当前值
                    cumulativemonth = (lastcumulativemonth * wt_lastcumulativemonth + value * wt_value) / (
                            wt_lastcumulativemonth + wt_value
                    )
                if not (date.month % 3 == 1 and date.day == 1):  # 判断是否所在季度第一天
                    cumulativequarter = (lastcumulativequarter * wt_lastcumulativequarter + value * wt_value) / (
                            wt_lastcumulativequarter + wt_value
                    )
                if not (date.month % 3 == 1 and date.day == 1):  # 判断是否所在季度第一天
                    cumulativehalfyear = (lastcumulativehalfyear * wt_lastcumulativehalfyear + value * wt_value) / (
                            wt_lastcumulativehalfyear + wt_value
                    )
                cumulativeyear = (cumulativeyear * lastcumulativeyear + value * wt_value) / (
                        wt_lastcumulativeyear + wt_value
                )
        if target.cycletype == "11":
            # 月报
            if date.month > 1:
                last_month_date = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0) + \
                                  datetime.timedelta(days=-1)
                if date.month > 3:  # 不是第一个季度
                    last_month_on_quarter = last_month_date.month % 3
                else:
                    last_month_on_quarter = last_month_date.month
                if last_month_on_quarter > 0:  # 任何一季度首月季累计为当前值
                    cumulativequarter = (lastcumulativequarter * wt_lastcumulativequarter + value * wt_value) / (
                            wt_lastcumulativequarter + wt_value
                    )
                if date.month != 7:  # 不是半年第一月
                    cumulativehalfyear = (lastcumulativehalfyear * wt_lastcumulativehalfyear + value * wt_value) / (
                            wt_lastcumulativehalfyear + wt_value
                    )
                cumulativeyear = (lastcumulativeyear + wt_lastcumulativeyear + value * wt_value) / (
                        wt_lastcumulativeyear + wt_value
                )
        if target.cycletype == "12":
            # 季报
            if date.month > 3:  # 非第一季度
                cumulativequarter = (lastcumulativequarter * wt_lastcumulativequarter + value * wt_value) / (
                        wt_lastcumulativequarter + wt_value
                )
                if date.month in [4, 5, 6, 10, 11, 12]:  # 半年后季
                    cumulativehalfyear = (lastcumulativehalfyear * wt_lastcumulativehalfyear + value * wt_value) / (
                            wt_lastcumulativehalfyear + wt_value
                    )
                cumulativeyear = (lastcumulativeyear * wt_lastcumulativeyear + value * wt_value) / (
                        wt_lastcumulativeyear + wt_value
                )
        if target.cycletype == "13":
            if date.month > 6:
                cumulativeyear = (lastcumulativeyear * wt_lastcumulativeyear + value * wt_value) / (
                        wt_lastcumulativeyear + wt_value
                )
        if target.cycletype == "14":
            pass
    if cumulative == '4':  # 非零算术平均
        if target.cycletype == "10":
            # 日报
            yestoday_date = date + datetime.timedelta(days=-1)
            if date.year == yestoday_date.year:
                # 当月昨天天数、当季到昨天的天数、半年到昨天的天数、当年到昨天的天数
                def get_days(start_time, end_time):
                    return int(
                        (end_time.replace(hour=0, minute=0, second=0, microsecond=0) - start_time.replace(
                            day=1, hour=0, minute=0, second=0, microsecond=0
                        )).total_seconds() / (60 * 60 * 24)
                    ) + 1

                now = datetime.datetime.now()

                # 1.当月昨天的天数
                if date.day > 1:  # 日报月初月累计为当前值
                    if lastcumulativemonth:
                        cumulativemonth = ((lastcumulativemonth * (date.day - 1)) + value) / date.day
                # 2.当季到昨天的天数
                # 判断当前月所在季度，第一季度/非第一季度
                if date.month <= 3:
                    days_in_quarter = get_days(now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
                                               yestoday_date)
                    if lastcumulativequarter:
                        cumulativequarter = (lastcumulativequarter * days_in_quarter + value) / (days_in_quarter + 1)
                else:
                    # 判断是否所在季度第一天
                    if not (date.month % 3 == 1 and date.day == 1):
                        # 当季到昨天的天数 = 昨天天数 - 上季度末天数
                        m_month = (date.month - 1) - (date.month - 1) % 3 + 1  # 10
                        m_newdate = datetime.datetime(date.year, m_month, 1)
                        days_in_quarter = get_days(
                            m_newdate.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
                            yestoday_date)
                        if lastcumulativequarter:
                            cumulativequarter = (lastcumulativequarter * days_in_quarter + value) / (
                                    days_in_quarter + 1)
                # 3.半年到昨天的天数(区分前/后半年)
                if date.month - 6 < 0:
                    days_in_halfyear = get_days(now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
                                                yestoday_date)
                    if lastcumulativehalfyear:
                        cumulativehalfyear = (lastcumulativehalfyear * days_in_halfyear + value) / (
                                days_in_halfyear + 1)
                else:
                    # 判断是否后半年的第一天
                    if not (date.month == 7 and date.day == 1):
                        # 半年到昨天的天数 = 昨天天数 - 上半年末天数
                        h_month = (date.month - 1) - (date.month - 1) % 6 + 1  # 10
                        h_newdate = datetime.datetime(date.year, h_month, 1)
                        days_in_halfyear = get_days(
                            h_newdate.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
                            yestoday_date)
                        if lastcumulativehalfyear:
                            cumulativehalfyear = (lastcumulativehalfyear * days_in_halfyear + value) / (
                                    days_in_halfyear + 1)
                # 4.当年到昨天的天数
                days_in_year = get_days(now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
                                        yestoday_date)
                if lastcumulativeyear:
                    cumulativeyear = (lastcumulativeyear * days_in_year + value) / days_in_year + 1
            else:
                pass
        if target.cycletype == "11":
            # 月报
            if date.month > 1:
                last_month_date = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0) + \
                                  datetime.timedelta(days=-1)
                # 1.上个月份
                # last_months = last_month_date.month
                # cumulativemonth = (lastcumulativemonth * last_months + value) / (last_months + 1)
                # 2.当季上个月所在月份
                if date.month > 3:  # 不是第一个季度
                    last_month_on_quarter = last_month_date.month % 3
                else:
                    last_month_on_quarter = last_month_date.month
                if last_month_on_quarter > 0:  # 任何一季度首月季累计为当前值
                    if lastcumulativequarter:
                        cumulativequarter = (lastcumulativequarter * last_month_on_quarter + value) / (
                                last_month_on_quarter + 1)
                # 3.半年上个月所在月份(区分前/后半年)
                last_month_on_halfyear = -1
                if date.month > 6:
                    if date.month - 6 > 1:
                        last_month_on_halfyear = last_month_date.month - 6
                else:
                    last_month_on_halfyear = last_month_date.month
                if last_month_on_halfyear != -1:
                    if lastcumulativehalfyear:
                        cumulativehalfyear = (lastcumulativehalfyear * last_month_on_halfyear + value) / (
                                last_month_on_halfyear + 1)
                # 4.年上个月所在月份
                last_month_on_year = last_month_date.month
                if lastcumulativeyear:
                    cumulativeyear = (lastcumulativeyear * last_month_on_year + value) / (last_month_on_year + 1)
            else:
                pass
        if target.cycletype == "12":
            # 季报
            if date.month > 3:  # 非第一季度
                q_month = (date.month - 1) - (date.month - 1) % 3 + 1  # 10
                q_newdate = datetime.datetime(date.year, q_month, 1)
                last_quarter_date = q_newdate + datetime.timedelta(days=-1)

                # 1.上个季度
                last_quarters = last_quarter_date.month // 3
                if lastcumulativequarter:
                    cumulativequarter = (lastcumulativequarter * last_quarters + value) / (last_quarters + 1)
                # 2.半年所在季度(区分前/后半年)
                if date.month in [4, 5, 6, 10, 11, 12]:
                    quarter_on_halfyear = 1
                    if lastcumulativehalfyear:
                        cumulativehalfyear = (lastcumulativehalfyear * quarter_on_halfyear + value) / (
                                quarter_on_halfyear + 1)
                # 3.年所在季度
                quarter_on_year = last_quarter_date.month // 3
                if lastcumulativeyear:
                    cumulativeyear = (lastcumulativeyear * quarter_on_year + value) / (quarter_on_year + 1)
        if target.cycletype == "13":
            if date.month > 6:
                if lastcumulativeyear:
                    cumulativeyear = (lastcumulativeyear + value) / 2
        if target.cycletype == "14":
            # 年报均为当前值
            pass
    # 处理保留位数
    try:
        cumulativemonth = round(cumulativemonth, target.digit)
    except:
        pass
    try:
        cumulativequarter = round(cumulativequarter, target.digit)
    except:
        pass
    try:
        cumulativehalfyear = round(cumulativehalfyear, target.digit)
    except:
        pass
    try:
        cumulativeyear = round(cumulativeyear, target.digit)
    except:
        pass
    return {"cumulativemonth": cumulativemonth, "cumulativequarter": cumulativequarter,
            "cumulativehalfyear": cumulativehalfyear, "cumulativeyear": cumulativeyear}


def getcalculatedata(target, date, guid, all_constant, all_target, tableList, forward=True):
    """
    数据计算
    @forward {bool}: 是否往前计算
    """
    curvalue = -9999
    if target.data_from == 'et':
        # 外部系统，直接取数
        # 从数据库中获取，取第一个值，其他情况抛错
        ret = Extract.getDataFromSource(target, date)
        if ret['result']:
            try:
                curvalue = float(ret['result'][0][0])
            except Exception as e:
                print(e)
            else:
                pass
    else:
        formula = ""

        # 本地系统根据公式计算
        if target.formula is not None:
            formula = target.formula

        # 从公式中提取指标与d:D
        members = formula.split('>')
        for member in members:
            if member.replace(" ", "") != "":
                col = "d"
                cond = "D"
                if (member.find('<') >= 0):
                    membertarget = member[member.find('<') + 1:].replace(" ", "")
                    th = membertarget
                    if membertarget.find(':') > 0:
                        col = membertarget[membertarget.find(':') + 1:]
                        membertarget = membertarget[0:membertarget.find(':')]
                        if col.find(':') > 0:
                            cond = col[col.find(':') + 1:]
                            col = col[0:col.find(':')]

                    # 查询常数库value值
                    # 公式中取常数值，不存在则取指标值
                    value = ""
                    isconstant = False
                    for constant in all_constant:
                        if membertarget == constant['code']:
                            value = constant['value']
                            isconstant = True
                            break
                    if not isconstant:
                        istarget = False
                        newtarget = None
                        for new_target in all_target:
                            if membertarget == new_target.code:
                                istarget = True
                                newtarget = new_target
                                break
                        if not istarget or newtarget is None:
                            formula = "-9999"
                            break
                        else:
                            # 同一应用，同一周期，同一业务，计算操作类型，guid不同(未计算过)的指标，先计算
                            # 即：当前指标由另一个公式中其他指标计算所得，'其他'指标值未计算出结果，先计算
                            #     A = B + 1 B未计算出，先计算出B
                            membertarget = newtarget
                            # 指标为加权指标先计算
                            cumulative = membertarget.cumulative

                            if forward:
                                if cumulative == '3':
                                    wt_membertarget = membertarget.weight_target
                                    getcalculatedata(wt_membertarget, date, guid, all_constant, all_target, tableList)

                                if membertarget.operationtype == target.operationtype and membertarget.adminapp_id == target.adminapp_id \
                                        and membertarget.cycletype == target.cycletype and membertarget.work_id == target.work_id \
                                        and membertarget.calculateguid != guid and not (cond.startswith('L') or cond.startswith('S')):  # 判断指标公式非当前周期的数据:
                                    getcalculatedata(membertarget, date, guid, all_constant, all_target, tableList)

                            # 取当年表
                            queryset = tableList["Entrydata"].objects
                            operationtype = membertarget.operationtype
                            if operationtype == "1":
                                queryset = tableList["Meterdata"].objects
                            if operationtype == "15":
                                queryset = tableList["Entrydata"].objects
                            if operationtype == "16":
                                queryset = tableList["Extractdata"].objects
                            if operationtype == "17":
                                queryset = tableList["Calculatedata"].objects
                            # 取去年表
                            if cond == "LYS" or cond == "LYE" or (
                                    (cond == "LSS" or cond == "LSE") and int(date.month) < 4) or (
                                    (cond == "LHS" or cond == "LHE") and int(date.month) < 7) or (
                                    (cond == "LMS" or cond == "LME" or cond == "SLME") and int(date.month) < 2):
                                tableyear = str(int(date.year) - 1)

                                if operationtype == "1":
                                    queryset = getmodels("Meterdata", tableyear).objects
                                if operationtype == "15":
                                    queryset = getmodels("Entrydata", tableyear).objects
                                if operationtype == "16":
                                    queryset = getmodels("Extractdata", tableyear).objects
                                if operationtype == "17":
                                    queryset = getmodels("Calculatedata", tableyear).objects

                            # 过滤时间
                            condtions = {'datadate': date}
                            if cond == "D":
                                condtions = {'datadate': date}
                            if cond == "M":
                                condtions = {'datadate__year': date.year, 'datadate__month': date.month}
                            if cond == "Y":
                                condtions = {'datadate__year': date.year}
                            if cond == "L":
                                newdate = date + datetime.timedelta(days=-1)
                                condtions = {'datadate': newdate}

                            if cond == "MS":
                                newdate = date.replace(day=1)
                                condtions = {'datadate': newdate}
                            if cond == "ME":
                                year = date.year
                                month = date.month
                                a, b = calendar.monthrange(year, month)  # a,b——weekday的第一天是星期几（0-6对应星期一到星期天）和这个月的所有天数
                                newdate = datetime.datetime(year=year, month=month, day=b)  # 构造本月月末datetime
                                condtions = {'datadate': newdate}
                            if cond == "LME":
                                date_now = date.replace(day=1)
                                newdate = date_now + datetime.timedelta(days=-1)
                                condtions = {'datadate': newdate}
                            if cond == "LMS":
                                date_now = date.replace(day=1)
                                date_now = date_now + datetime.timedelta(days=-1)
                                newdate = datetime.datetime(date_now.year, date_now.month, 1)
                                condtions = {'datadate': newdate}

                            if cond == "YS":
                                newdate = date.replace(month=1, day=1)
                                condtions = {'datadate': newdate}
                            if cond == "YE":
                                newdate = date.replace(month=12, day=31)
                                condtions = {'datadate': newdate}
                            if cond == "LYS":
                                newdate = date.replace(month=1, day=1)
                                newdate = newdate + datetime.timedelta(days=-1)
                                newdate = datetime.datetime(newdate.year, 1, 1)
                                condtions = {'datadate': newdate}
                            if cond == "LYE":
                                newdate = date.replace(month=1, day=1)
                                newdate = newdate + datetime.timedelta(days=-1)
                                condtions = {'datadate': newdate}

                            if cond == "SS":
                                month = (date.month - 1) - (date.month - 1) % 3 + 1
                                newdate = datetime.datetime(date.year, month, 1)
                                condtions = {'datadate': newdate}
                            if cond == "SE":
                                month = (date.month - 1) - (date.month - 1) % 3 + 1
                                if month == 10:
                                    newdate = datetime.datetime(date.year + 1, 1, 1) + datetime.timedelta(days=-1)
                                else:
                                    newdate = datetime.datetime(date.year, month + 3, 1) + datetime.timedelta(days=-1)
                                condtions = {'datadate': newdate}
                            if cond == "LSS":
                                month = (date.month - 1) - (date.month - 1) % 3 + 1
                                newdate = datetime.datetime(date.year, month, 1)
                                newdate = newdate + datetime.timedelta(days=-1)
                                newdate = datetime.datetime(newdate.year, newdate.month - 2, 1)
                                condtions = {'datadate': newdate}
                            if cond == "LSE":
                                month = (date.month - 1) - (date.month - 1) % 3 + 1  # 10
                                newdate = datetime.datetime(date.year, month, 1)
                                newdate = newdate + datetime.timedelta(days=-1)
                                condtions = {'datadate': newdate}

                            if cond == "HS":
                                month = (date.month - 1) - (date.month - 1) % 6 + 1
                                newdate = datetime.datetime(date.year, month, 1)
                                condtions = {'datadate': newdate}
                            if cond == "HE":
                                month = (date.month - 1) - (date.month - 1) % 6 + 1
                                if month == 7:
                                    newdate = datetime.datetime(date.year + 1, 1, 1) + datetime.timedelta(days=-1)
                                else:
                                    newdate = datetime.datetime(date.year, month + 6, 1) + datetime.timedelta(days=-1)
                                condtions = {'datadate': newdate}
                            if cond == "LHS":
                                month = (date.month - 1) - (date.month - 1) % 6 + 1
                                newdate = datetime.datetime(date.year, month, 1)
                                newdate = newdate + datetime.timedelta(days=-1)
                                newdate = datetime.datetime(newdate.year, newdate.month - 5, 1)
                                condtions = {'datadate': newdate}
                            if cond == "LHE":
                                month = (date.month - 1) - (date.month - 1) % 6 + 1
                                newdate = datetime.datetime(date.year, month, 1)
                                newdate = newdate + datetime.timedelta(days=-1)
                                condtions = {'datadate': newdate}
                            if cond == "SLME":
                                date_now = date.replace(day=1)
                                newdate = date_now + datetime.timedelta(days=-1)
                                condtions = {'datadate': newdate}

                            new_date = ""
                            if cond == "MAVG" or cond == "MMAX" or cond == "MMIN":
                                ms_newdate = date.replace(day=1)
                                me_newdate = date
                                new_date = (ms_newdate, me_newdate)

                            if cond == "SAVG" or cond == "SMAX" or cond == "SMIN":
                                month = (date.month - 1) - (date.month - 1) % 3 + 1
                                ss_newdate = datetime.datetime(date.year, month, 1)
                                se_newdate = date
                                new_date = (ss_newdate, se_newdate)

                            if cond == "HAVG" or cond == "HMAX" or cond == "HMIN":
                                month = (date.month - 1) - (date.month - 1) % 6 + 1
                                hs_newdate = datetime.datetime(date.year, month, 1)
                                he_newdate = date
                                new_date = (hs_newdate, he_newdate)

                            if cond == "YAVG" or cond == "YMAX" or cond == "YMIN":
                                ys_newdate = date.replace(month=1, day=1)
                                ye_newdate = date
                                new_date = (ys_newdate, ye_newdate)

                            query_res = []
                            if condtions:
                                newdate = condtions['datadate']
                                query_res = queryset.filter(**condtions).filter(target=membertarget).exclude(state="9")
                            if new_date:
                                query_res = queryset.filter(datadate__range=new_date).filter(
                                    target=membertarget).exclude(state="9")
                            if len(query_res) <= 0:
                                value = 0
                            else:
                                # 获取季累计、年累计等字段值
                                value = 0
                                if col == 'd':
                                    if cond == "MAVG" or cond == "SAVG" or cond == "HAVG" or cond == "YAVG":
                                        value = query_res.aggregate(Avg('curvalue'))["curvalue__avg"]
                                    elif cond == "MMAX" or cond == "SMAX" or cond == "HMAX" or cond == "YMAX":
                                        value = query_res.aggregate(Max('curvalue'))["curvalue__max"]
                                    elif cond == "MMIN" or cond == "SMIN" or cond == "HMIN" or cond == "YMIN":
                                        value = query_res.aggregate(Min('curvalue'))["curvalue__min"]
                                    elif cond == "SLME" and newdate.month in [12, 3, 6,
                                                                              9]:  # 时间为本季上月末且当是每一季度第一个月的时候，值为0
                                        value = 0
                                    else:
                                        value = query_res[0].curvalue
                                if col == 'm':
                                    if cond == "MAVG" or cond == "SAVG" or cond == "HAVG" or cond == "YAVG":
                                        value = query_res.aggregate(Avg('cumulativemonth'))["cumulativemonth__avg"]
                                    elif cond == "MMAX" or cond == "SMAX" or cond == "HMAX" or cond == "YMAX":
                                        value = query_res.aggregate(Max('cumulativemonth'))["cumulativemonth__max"]
                                    elif cond == "MMIN" or cond == "SMIN" or cond == "HMIN" or cond == "YMIN":
                                        value = query_res.aggregate(Min('cumulativemonth'))["cumulativemonth__min"]
                                    elif cond == "SLME" and newdate.month in [12, 3, 6, 9]:
                                        value = 0
                                    else:
                                        value = query_res[0].cumulativemonth
                                if col == 's':
                                    if cond == "MAVG" or cond == "SAVG" or cond == "HAVG" or cond == "YAVG":
                                        value = query_res.aggregate(Avg('cumulativequarter'))["cumulativequarter__avg"]
                                    elif cond == "MMAX" or cond == "SMAX" or cond == "HMAX" or cond == "YMAX":
                                        value = query_res.aggregate(Max('cumulativequarter'))["cumulativequarter__max"]
                                    elif cond == "MMIN" or cond == "SMIN" or cond == "HMIN" or cond == "YMIN":
                                        value = query_res.aggregate(Min('cumulativequarter'))["cumulativequarter__min"]
                                    elif cond == "SLME" and newdate.month in [12, 3, 6, 9]:
                                        value = 0
                                    else:
                                        value = query_res[0].cumulativequarter
                                if col == 'h':
                                    if cond == "MAVG" or cond == "SAVG" or cond == "HAVG" or cond == "YAVG":
                                        value = query_res.aggregate(Avg('cumulativehalfyear'))[
                                            "cumulativehalfyear__avg"]
                                    elif cond == "MMAX" or cond == "SMAX" or cond == "HMAX" or cond == "YMAX":
                                        value = query_res.aggregate(Max('cumulativehalfyear'))[
                                            "cumulativehalfyear__max"]
                                    elif cond == "MMIN" or cond == "SMIN" or cond == "HMIN" or cond == "YMIN":
                                        value = query_res.aggregate(Min('cumulativehalfyear'))[
                                            "cumulativehalfyear__min"]
                                    elif cond == "SLME" and newdate.month in [12, 3, 6, 9]:
                                        value = 0
                                    else:
                                        value = query_res[0].cumulativehalfyear
                                if col == 'y':
                                    if cond == "MAVG" or cond == "SAVG" or cond == "HAVG" or cond == "YAVG":
                                        value = query_res.aggregate(Avg('cumulativeyear'))["cumulativeyear__avg"]
                                    elif cond == "MMAX" or cond == "SMAX" or cond == "HMAX" or cond == "YMAX":
                                        value = query_res.aggregate(Max('cumulativeyear'))["cumulativeyear__max"]
                                    elif cond == "MMIN" or cond == "SMIN" or cond == "HMIN" or cond == "YMIN":
                                        value = query_res.aggregate(Min('cumulativeyear'))["cumulativeyear__min"]
                                    elif cond == "SLME" and newdate.month in [12, 3, 6, 9]:
                                        value = 0
                                    else:
                                        value = query_res[0].cumulativeyear
                    # 公式中指标替换成值
                    formula = formula.replace("<" + th + ">", str(value))

        # 根据公式计算出值
        try:
            curvalue = eval(formula)
        except:
            pass

    calculatedata = tableList["Calculatedata"].objects.exclude(state="9").filter(target_id=target.id).filter(
        datadate=date)
    if len(calculatedata) > 0:
        calculatedata = calculatedata[0]
    else:
        calculatedata = tableList["Calculatedata"]()
    calculatedata.target = target
    calculatedata.datadate = date
    # 根据倍率与保留位数得出最后的值
    calculatedata.curvalue = curvalue
    calculatedata.curvalue = decimal.Decimal(str(float(calculatedata.curvalue))) * decimal.Decimal(
        str(float(target.magnification)))
    calculatedata.curvalue = decimal.Decimal(str(calculatedata.curvalue)).quantize(decimal.Decimal(Digit(target.digit)),
                                                                                   rounding=decimal.ROUND_HALF_UP)
    # 累计值计算
    if target.cumulative in ['1', '2', '3', '4']:
        cumulative = getcumulative(tableList, target, date, decimal.Decimal(str(calculatedata.curvalue)))
        calculatedata.cumulativemonth = cumulative["cumulativemonth"]
        calculatedata.cumulativequarter = cumulative["cumulativequarter"]
        calculatedata.cumulativehalfyear = cumulative["cumulativehalfyear"]
        calculatedata.cumulativeyear = cumulative["cumulativeyear"]
    # 保存最终计算公式
    calculatedata.formula = target.formula
    calculatedata.save()
    # 保存该次计算guid，不再参与本次计算
    target.calculateguid = guid
    target.save()


def ajax_cumulate(request):
    if request.user.is_authenticated():
        cur_value = request.POST.get('cur_value', '')
        target_id = request.POST.get('target_id', '')
        reporting_date = request.POST.get('reporting_date', '')
        cycletype = request.POST.get('cycletype', '')
        result = {}

        try:
            reporting_date = getreporting_date(reporting_date, cycletype)
        except:
            result['status'] = 0
            result['data'] = "报表日期处理出错。"
        else:
            try:
                target = Target.objects.get(id=int(target_id))
            except:
                result['status'] = 0
                result['data'] = "当前指标不存在。"
            else:
                tableyear = str(reporting_date.year)
                tableList = {
                    "Entrydata": getmodels("Entrydata", tableyear),
                    "Meterdata": getmodels("Meterdata", tableyear),
                    "Extractdata": getmodels("Extractdata", tableyear),
                    "Calculatedata": getmodels("Calculatedata", tableyear)
                }

                cumulative = getcumulative(tableList, target, reporting_date, decimal.Decimal(str(cur_value)))
                cumulativemonth = cumulative["cumulativemonth"]
                cumulativequarter = cumulative["cumulativequarter"]
                cumulativehalfyear = cumulative["cumulativehalfyear"]
                cumulativeyear = cumulative["cumulativeyear"]

                result['status'] = 1
                result['data'] = {
                    "cumulativemonth": cumulativemonth,
                    "cumulativequarter": cumulativequarter,
                    "cumulativehalfyear": cumulativehalfyear,
                    "cumulativeyear": cumulativeyear
                }

        return JsonResponse(result)
    else:
        return HttpResponseRedirect('/login')


def single_reextract(request):
    """
    对单个指标重新提取
    """
    if request.user.is_authenticated():
        status = 1
        info = "重新提取成功"

        target_id = request.POST.get("target_id", "")
        reporting_date = request.POST.get('reporting_date', '')

        try:
            c_target = Target.objects.get(id=int(target_id))
        except:
            status = 0
            info = "当前指标不存在"
        else:
            cycletype = c_target.cycletype
            operationtype = c_target.operationtype

            try:
                reporting_date = getreporting_date(reporting_date, cycletype)
            except:
                status = 0
                info = "时间处理异常"
            else:
                tableyear = str(reporting_date.year)

                EntryTable = getmodels("Entrydata", tableyear)
                MeterTable = getmodels("Meterdata", tableyear)
                ExtractTable = getmodels("Extractdata", tableyear)
                CalculateTable = getmodels("Calculatedata", tableyear)
                tableList = {"Entrydata": EntryTable, "Meterdata": MeterTable, "Extractdata": ExtractTable,
                             "Calculatedata": CalculateTable}

                # 根据指标周期修改reporting_date
                a_cycle_aft_date = get_a_cycle_aft(reporting_date, cycletype)
                if operationtype == "16":
                    extractdata = getmodels("Extractdata", str(reporting_date.year)).objects.exclude(state="9").filter(
                        target_id=c_target.id).filter(datadate=reporting_date)
                    if len(extractdata) > 0:
                        extractdata = extractdata[0]
                        tablename = ""
                        try:
                            tablename = c_target.storage.tablename
                        except:
                            pass

                        rows = []
                        if tablename:
                            try:
                                with connection.cursor() as cursor:
                                    reporting_date_stf = reporting_date.strftime("%Y-%m-%d %H:%M:%S")
                                    strsql = "SELECT curvalue FROM {tablename} WHERE target_id='{target_id}' AND datadate='{datadate}' ORDER BY id DESC".format(
                                        tablename=tablename, target_id=c_target.id, datadate=reporting_date_stf
                                    )
                                    cursor.execute(strsql)
                                    rows = cursor.fetchall()
                                connection.close()
                            except Exception as e:
                                pass
                            if len(rows) > 0:
                                try:
                                    if c_target.is_repeat == '2':
                                        rownum = 0
                                        rowvalue = 0
                                        for row in rows:
                                            if row[0] is not None:
                                                rowvalue += row[0]
                                                rownum += 1
                                        extractdata.curvalue = rowvalue / rownum
                                    else:
                                        extractdata.curvalue = rows[0][0]
                                    extractdata.curvalue = decimal.Decimal(
                                        float(extractdata.curvalue) * float(c_target.magnification))
                                    extractdata.curvalue = round(extractdata.curvalue, c_target.digit)
                                except:
                                    pass
                        if not rows or not c_target.cycle:  # 没取到数据 或者 没有取数周期，根据数据源实时取
                            ret = Extract.getDataFromSource(c_target, a_cycle_aft_date)
                            result_list = ret["result"]
                            if result_list:
                                try:
                                    if c_target.is_repeat == '2':
                                        rownum = 0
                                        rowvalue = 0
                                        for row in result_list:
                                            if row[0] is not None:
                                                rowvalue += row[0]
                                                rownum += 1
                                        extractdata.curvalue = rowvalue / rownum
                                    else:
                                        extractdata.curvalue = result_list[0][0]
                                    extractdata.curvalue = decimal.Decimal(
                                        float(extractdata.curvalue) * float(c_target.magnification))
                                    extractdata.curvalue = round(extractdata.curvalue, c_target.digit)
                                except Exception as e:
                                    print(e)

                        if c_target.cumulative in ['1', '2', '3', '4']:
                            cumulative = getcumulative(tableList, c_target, reporting_date, extractdata.curvalue)
                            extractdata.cumulativemonth = cumulative["cumulativemonth"]
                            extractdata.cumulativequarter = cumulative["cumulativequarter"]
                            extractdata.cumulativehalfyear = cumulative["cumulativehalfyear"]
                            extractdata.cumulativeyear = cumulative["cumulativeyear"]
                        extractdata.save()
                        info = "{0}{1}".format(c_target.name, info)
            return JsonResponse({
                "status": status,
                "info": info,
            })


def recalculate_targets_formula_contains(target, date, guid, all_constant, all_target, tableList, contains_self=True):
    """
    重新计算包括当前指标的计算指标
    @param target:
    @param date:
    @param guid: 一致表示参与过计算
    @param all_constant:
    @param all_target:
    @param tableList:
    @param contains_self: 是否重新计算当前指标
    @return:
    """
    try:
        all_targets = all_target.exclude(calculateguid=guid)
        if contains_self:  # 计算当前指标
            getcalculatedata(target, date, guid, all_constant, all_target, tableList, forward=False)

        # 后续指标
        for t in all_targets:
            if t.operationtype == "17":
                ts_contained = get_targets_from_formula(t.formula)
                if target.code in ts_contained and t.calculateguid != guid:
                    recalculate_targets_formula_contains(t, date, guid, all_constant, all_target, tableList)
    except Exception as e:
        print(e)
        return False
    return True


def single_recalculate(request):
    if request.user.is_authenticated():
        target_id = request.POST.get("target_id", "")
        reporting_date = request.POST.get('reporting_date', '')
        recalculate_type = request.POST.get('recalculate_type', '')
        status = 1
        info = "重新计算成功"
        try:
            c_target = Target.objects.get(id=int(target_id))
        except:
            status = 0
            info = "当前指标不存在"
        else:
            cycletype = c_target.cycletype
            operationtype = c_target.operationtype

            try:
                reporting_date = getreporting_date(reporting_date, cycletype)
            except:
                status = 0
                info = "时间处理异常"
            else:
                if operationtype == "17":
                    guid = uuid.uuid1()
                    all_constant = Constant.objects.exclude(state="9").values()
                    all_target = Target.objects.exclude(state="9")
                    tableyear = str(reporting_date.year)

                    EntryTable = getmodels("Entrydata", tableyear)
                    MeterTable = getmodels("Meterdata", tableyear)
                    ExtractTable = getmodels("Extractdata", tableyear)
                    CalculateTable = getmodels("Calculatedata", tableyear)
                    tableList = {
                        "Entrydata": EntryTable,
                        "Meterdata": MeterTable,
                        "Extractdata": ExtractTable,
                        "Calculatedata": CalculateTable
                    }

                    if recalculate_type == "1":
                        ret = recalculate_targets_formula_contains(c_target, reporting_date, guid, all_constant, all_target, tableList)
                    else:
                        ret = recalculate_targets_formula_contains(c_target, reporting_date, guid, all_constant, all_target, tableList, contains_self=False)
                    if not ret:
                        status = 0
                        info = "指标{0}重新计算失败".format(c_target.name)
                else:
                    status = 0
                    info = "该指标不是计算指标"

        return JsonResponse({
            "status": status,
            "info": info,
        })


def reporting_formulacalculate(request):
    if request.user.is_authenticated():
        id = request.POST.get('id', '')
        cycletype = request.POST.get('cycletype', '')
        reporting_date = request.POST.get('reporting_date', '')
        try:
            id = int(id)
            reporting_date = getreporting_date(reporting_date, cycletype)
        except:
            return HttpResponse(0)
        date = reporting_date

        all_constant = Constant.objects.exclude(state="9")
        constant_codename = {}
        for constant in all_constant:
            code = constant.code
            name = constant.name
            constant_codename[code] = name

        all_target = Target.objects.exclude(state="9")
        target_codename = {}
        for target in all_target:
            code = target.code
            name = target.name
            target_codename[code] = name
        data_field = {"d": "当前值", "m": "月累积", "s": "季累积", "h": "半年累积", "y": "年累积", "c": "常数"}
        data_time = {
            "D": "当天", "L": "前一天", "MS": "月初", "ME": "月末", "LMS": "上月初", "LME": "上月末",
            "SS": "季初", "SE": "季末", "LSS": "上季初", "LSE": "上季末", "HS": "半年初", "HE": "半年末",
            "LHS": "前个半年初", "LHE": "前个半年末", "YS": "年初", "YE": "年末", "LYS": "去年初",
            "LYE": "去年末", "MAVG": "月平均值", "SAVG": "季平均值", "HAVG": "半年平均值", "YAVG": "年均值",
            "MMAX": "月最大值", "MMIN": "月最小值", "SMAX": "季最大值", "SMIN": "季最小值",
            "HMAX": "半年最大值", "HMIN": "半年最小值", "YMAX": "年最大值", "YMIN": "年最小值", "SLME": "本季上月末"
        }

        calculatedata = getmodels("Calculatedata", str(date.year)).objects.exclude(state="9").filter(
            id=id).select_related("target")
        if len(calculatedata) > 0:
            formula = calculatedata[0].formula
            target = calculatedata[0].target
            data_from = target.data_from if target else 'lc'

            if data_from == 'lc':
                if formula is not None:
                    formula = formula.replace(" ", "")
                formula_chinese = formula + " = " + str(round(calculatedata[0].curvalue, calculatedata[0].target.digit))
                members = formula.split('>')
                for member in members:
                    if member.replace(" ", "") != "":
                        if (member.find('<') >= 0):
                            col = "d"
                            cond = "D"
                            membertarget = member[member.find('<') + 1:]
                            target_english = '<' + membertarget + '>'
                            if membertarget.find(':') > 0:
                                col = membertarget[membertarget.find(':') + 1:]
                                membertarget = membertarget[0:membertarget.find(':')]
                                if col.find(':') > 0:
                                    cond = col[col.find(':') + 1:]
                                    col = col[0:col.find(':')]

                            value = ""
                            if membertarget in constant_codename:
                                constant_name = constant_codename[membertarget]
                                constant_col = data_field[col]
                                memberconstant = Constant.objects.filter(code=membertarget).exclude(state="9")
                                if len(memberconstant) <= 0:
                                    value = 0
                                else:
                                    memberconstant = memberconstant[0]
                                    value = memberconstant.value
                                value = "{:f}".format(decimal.Decimal(str(value) if str(value) else "0").normalize())
                                constant_chinese = '<' + constant_name + ':' + constant_col + '>(' + value + ')'
                                formula_chinese = formula_chinese.replace(target_english, constant_chinese)

                            else:
                                target_name = membertarget
                                try:
                                    target_name = target_codename[membertarget]
                                except:
                                    pass
                                target_col = data_field[col]
                                target_cond = data_time[cond]

                                membertarget = Target.objects.filter(code=membertarget).exclude(state="9")

                                childid = None
                                if len(membertarget) <= 0:
                                    value = "指标不存在"
                                else:
                                    membertarget = membertarget[0]

                                    tableyear = str(date.year)
                                    queryset = getmodels("Entrydata", tableyear).objects
                                    if cond == "LYS" or cond == "LYE" or (
                                            (cond == "LSS" or cond == "LSE") and int(date.month) < 4) or (
                                            (cond == "LHS" or cond == "LHE") and int(date.month) < 7) or (
                                            (cond == "LMS" or cond == "LME" or cond == "SLME") and int(date.month) < 2):
                                        tableyear = str(int(date.year) - 1)
                                    operationtype = membertarget.operationtype
                                    if operationtype == "1":
                                        queryset = getmodels("Meterdata", tableyear).objects
                                    if operationtype == "15":
                                        queryset = getmodels("Entrydata", tableyear).objects
                                    if operationtype == "16":
                                        queryset = getmodels("Extractdata", tableyear).objects
                                    if operationtype == "17":
                                        queryset = getmodels("Calculatedata", tableyear).objects
                                    condtions = {'datadate': date}
                                    if cond == "D":
                                        condtions = {'datadate': date}
                                    if cond == "M":
                                        condtions = {'datadate__year': date.year, 'datadate__month': date.month}
                                    if cond == "Y":
                                        condtions = {'datadate__year': date.year}
                                    if cond == "L":
                                        newdate = date + datetime.timedelta(days=-1)
                                        condtions = {'datadate': newdate}

                                    if cond == "MS":
                                        newdate = date.replace(day=1)
                                        condtions = {'datadate': newdate}
                                    if cond == "ME":
                                        year = date.year
                                        month = date.month
                                        a, b = calendar.monthrange(year, month)
                                        newdate = datetime.datetime(year=year, month=month, day=b)
                                        condtions = {'datadate': newdate}
                                    if cond == "LME":
                                        date_now = date.replace(day=1)
                                        newdate = date_now + datetime.timedelta(days=-1)
                                        condtions = {'datadate': newdate}
                                    if cond == "LMS":
                                        date_now = date.replace(day=1)
                                        date_now = date_now + datetime.timedelta(days=-1)
                                        newdate = datetime.datetime(date_now.year, date_now.month, 1)
                                        condtions = {'datadate': newdate}

                                    if cond == "YS":
                                        newdate = date.replace(month=1, day=1)
                                        condtions = {'datadate': newdate}
                                    if cond == "YE":
                                        newdate = date.replace(month=12, day=31)
                                        condtions = {'datadate': newdate}
                                    if cond == "LYS":
                                        newdate = date.replace(month=1, day=1)
                                        newdate = newdate + datetime.timedelta(days=-1)
                                        newdate = datetime.datetime(newdate.year, 1, 1)
                                        condtions = {'datadate': newdate}
                                    if cond == "LYE":
                                        newdate = date.replace(month=1, day=1)
                                        newdate = newdate + datetime.timedelta(days=-1)
                                        condtions = {'datadate': newdate}

                                    if cond == "SS":
                                        month = (date.month - 1) - (date.month - 1) % 3 + 1
                                        newdate = datetime.datetime(date.year, month, 1)
                                        condtions = {'datadate': newdate}
                                    if cond == "SE":
                                        month = (date.month - 1) - (date.month - 1) % 3 + 1
                                        if month == 10:
                                            newdate = datetime.datetime(date.year + 1, 1, 1) + datetime.timedelta(
                                                days=-1)
                                        else:
                                            newdate = datetime.datetime(date.year, month + 3, 1) + datetime.timedelta(
                                                days=-1)
                                        condtions = {'datadate': newdate}
                                    if cond == "LSS":
                                        month = (date.month - 1) - (date.month - 1) % 3 + 1
                                        newdate = datetime.datetime(date.year, month, 1)
                                        newdate = newdate + datetime.timedelta(days=-1)
                                        newdate = datetime.datetime(newdate.year, newdate.month - 2, 1)
                                        condtions = {'datadate': newdate}
                                    if cond == "LSE":
                                        month = (date.month - 1) - (date.month - 1) % 3 + 1
                                        newdate = datetime.datetime(date.year, month, 1)
                                        newdate = newdate + datetime.timedelta(days=-1)
                                        condtions = {'datadate': newdate}

                                    if cond == "HS":
                                        month = (date.month - 1) - (date.month - 1) % 6 + 1
                                        newdate = datetime.datetime(date.year, month, 1)
                                        condtions = {'datadate': newdate}
                                    if cond == "HE":
                                        month = (date.month - 1) - (date.month - 1) % 6 + 1
                                        if month == 7:
                                            newdate = datetime.datetime(date.year + 1, 1, 1) + datetime.timedelta(
                                                days=-1)
                                        else:
                                            newdate = datetime.datetime(date.year, month + 6, 1) + datetime.timedelta(
                                                days=-1)
                                        condtions = {'datadate': newdate}
                                    if cond == "LHS":
                                        month = (date.month - 1) - (date.month - 1) % 6 + 1
                                        newdate = datetime.datetime(date.year, month, 1)
                                        newdate = newdate + datetime.timedelta(days=-1)
                                        newdate = datetime.datetime(newdate.year, newdate.month - 5, 1)
                                        condtions = {'datadate': newdate}
                                    if cond == "LHE":
                                        month = (date.month - 1) - (date.month - 1) % 6 + 1
                                        newdate = datetime.datetime(date.year, month, 1)
                                        newdate = newdate + datetime.timedelta(days=-1)
                                        condtions = {'datadate': newdate}
                                    if cond == "SLME":
                                        newdate = date.replace(day=1)
                                        newdate = newdate + datetime.timedelta(days=-1)
                                        condtions = {'datadate': newdate}

                                    new_date = ""
                                    if cond == "MAVG" or cond == "MMAX" or cond == "MMIN":
                                        ms_newdate = date.replace(day=1)
                                        me_newdate = date
                                        new_date = (ms_newdate, me_newdate)

                                    if cond == "SAVG" or cond == "SMAX" or cond == "SMIN":
                                        month = (date.month - 1) - (date.month - 1) % 3 + 1
                                        ss_newdate = datetime.datetime(date.year, month, 1)
                                        se_newdate = date
                                        new_date = (ss_newdate, se_newdate)

                                    if cond == "HAVG" or cond == "HMAX" or cond == "HMIN":
                                        month = (date.month - 1) - (date.month - 1) % 6 + 1
                                        hs_newdate = datetime.datetime(date.year, month, 1)
                                        he_newdate = date
                                        new_date = (hs_newdate, he_newdate)

                                    if cond == "YAVG" or cond == "YMAX" or cond == "YMIN":
                                        ys_newdate = date.replace(month=1, day=1)
                                        ye_newdate = date
                                        new_date = (ys_newdate, ye_newdate)

                                    query_res = []
                                    if condtions:
                                        newdate = condtions['datadate']
                                        query_res = queryset.filter(**condtions).filter(target=membertarget).exclude(
                                            state="9").select_related("target")
                                    if new_date:
                                        query_res = queryset.filter(datadate__range=new_date).filter(
                                            target=membertarget).exclude(state="9")

                                    if len(query_res) <= 0:
                                        if cond == "SLME" and newdate.month == 12:
                                            value = "0"
                                        else:
                                            value = "数据不存在"
                                    else:
                                        value = "0"
                                        if col == 'd':
                                            if cond == "MAVG" or cond == "SAVG" or cond == "HAVG" or cond == "YAVG":
                                                value = str(round(query_res.aggregate(Avg('curvalue'))["curvalue__avg"],
                                                                  query_res[0].target.digit))
                                            elif cond == "MMAX" or cond == "SMAX" or cond == "HMAX" or cond == "YMAX":
                                                value = str(round(query_res.aggregate(Max('curvalue'))["curvalue__max"],
                                                                  query_res[0].target.digit))
                                            elif cond == "MMIN" or cond == "SMIN" or cond == "HMIN" or cond == "YMIN":
                                                value = str(round(query_res.aggregate(Min('curvalue'))["curvalue__min"],
                                                                  query_res[0].target.digit))
                                            elif cond == "SLME" and newdate.month in [12, 3, 6, 9]:
                                                value = "0"
                                            else:
                                                value = str(round(query_res[0].curvalue, query_res[0].target.digit))
                                                if operationtype == "17":
                                                    childid = str(query_res[0].id)
                                        if col == 'm':
                                            if cond == "MAVG" or cond == "SAVG" or cond == "HAVG" or cond == "YAVG":
                                                value = str(
                                                    round(
                                                        query_res.aggregate(Avg('cumulativemonth'))[
                                                            'cumulativemonth__avg'],
                                                        query_res[0].target.digit))
                                            elif cond == "MMAX" or cond == "SMAX" or cond == "HMAX" or cond == "YMAX":
                                                value = str(round(
                                                    query_res.aggregate(Max('cumulativemonth'))["cumulativemonth__max"],
                                                    query_res[0].target.digit))
                                            elif cond == "MMIN" or cond == "SMIN" or cond == "HMIN" or cond == "YMIN":
                                                value = str(round(
                                                    query_res.aggregate(Min('cumulativemonth'))["cumulativemonth__min"],
                                                    query_res[0].target.digit))
                                            elif cond == "SLME" and newdate.month in [12, 3, 6, 9]:
                                                value = "0"
                                            else:
                                                value = str(
                                                    round(query_res[0].cumulativemonth, query_res[0].target.digit))
                                        if col == 's':
                                            if cond == "MAVG" or cond == "SAVG" or cond == "HAVG" or cond == "YAVG":
                                                value = str(
                                                    round(
                                                        query_res.aggregate(Avg('cumulativequarter'))[
                                                            'cumulativequarter__avg'],
                                                        query_res[0].target.digit))
                                            elif cond == "MMAX" or cond == "SMAX" or cond == "HMAX" or cond == "YMAX":
                                                value = str(round(
                                                    query_res.aggregate(Max('cumulativequarter'))[
                                                        "cumulativequarter__max"],
                                                    query_res[0].target.digit))
                                            elif cond == "MMIN" or cond == "SMIN" or cond == "HMIN" or cond == "YMIN":
                                                value = str(round(
                                                    query_res.aggregate(Min('cumulativequarter'))[
                                                        "cumulativequarter__min"],
                                                    query_res[0].target.digit))
                                            elif cond == "SLME" and newdate.month in [12, 3, 6, 9]:
                                                value = "0"
                                            else:
                                                value = str(
                                                    round(query_res[0].cumulativequarter, query_res[0].target.digit))
                                        if col == 'h':
                                            if cond == "MAVG" or cond == "SAVG" or cond == "HAVG" or cond == "YAVG":
                                                value = str(
                                                    round(query_res.aggregate(Avg('cumulativehalfyear'))[
                                                              'cumulativehalfyear__avg'],
                                                          query_res[0].target.digit))
                                            elif cond == "MMAX" or cond == "SMAX" or cond == "HMAX" or cond == "YMAX":
                                                value = str(round(query_res.aggregate(Max('cumulativehalfyear'))[
                                                                      "cumulativehalfyear__max"],
                                                                  query_res[0].target.digit))
                                            elif cond == "MMIN" or cond == "SMIN" or cond == "HMIN" or cond == "YMIN":
                                                value = str(round(query_res.aggregate(Min('cumulativehalfyear'))[
                                                                      "cumulativehalfyear__min"],
                                                                  query_res[0].target.digit))
                                            elif cond == "SLME" and newdate.month in [12, 3, 6, 9]:
                                                value = "0"
                                            else:
                                                value = str(
                                                    round(query_res[0].cumulativehalfyear, query_res[0].target.digit))
                                        if col == 'y':
                                            if cond == "MAVG" or cond == "SAVG" or cond == "HAVG" or cond == "YAVG":
                                                value = str(
                                                    round(query_res.aggregate(Avg('cumulativeyear'))[
                                                              'cumulativeyear__avg'],
                                                          query_res[0].target.digit))
                                            elif cond == "MMAX" or cond == "SMAX" or cond == "HMAX" or cond == "YMAX":
                                                value = str(
                                                    round(query_res.aggregate(Max('cumulativeyear'))[
                                                              "cumulativeyear__max"],
                                                          query_res[0].target.digit))
                                            elif cond == "MMIN" or cond == "SMIN" or cond == "HMIN" or cond == "YMIN":
                                                value = str(
                                                    round(query_res.aggregate(Min('cumulativeyear'))[
                                                              "cumulativeyear__min"],
                                                          query_res[0].target.digit))
                                            elif cond == "SLME" and newdate.month in [12, 3, 6, 9]:
                                                value = "0"
                                            else:
                                                value = str(
                                                    round(query_res[0].cumulativeyear, query_res[0].target.digit))

                                target_chinese = '<' + target_name + ':' + target_col + ':' + target_cond + '>(' + value + ')'
                                if childid:
                                    target_chinese = "<button id='formulabtn_" + childid + "' style=\"font-size:18px;color: #0a6aa1;padding-top:-5px\" type=\"button\" class=\"btn btn-link formulabtn\">" + target_chinese + "</button>"
                                formula_chinese = formula_chinese.replace(target_english, target_chinese)

                formula_chinese = "<div style=\"font-size:18px\"><span style=\"font-size:18px\"  class=\"label label-primary\"> " + \
                                  calculatedata[0].target.name + "</span>" + formula_chinese + "<br><br></div>"
                # "<span style=\"font-size:18px\"  class=\"label label-primary\">#1机组发电量" + aa + "</span><button id='formulabtn_" + aa + "' style=\"font-size:18px;color: #0a6aa1;padding-top:-5px\" type=\"button\" class=\"btn btn-link formulabtn\"><#1_发电量:当前值:当天>221.3</button> + <发电量:当前值:当天>+1+#1机组发电量</span> 123.2<#1_发电量:当前值:当天>+221.3<发电量:当前值:当天>+1=31.12<br><br></div>")
            else:
                formula_chinese = " 外部系统获得 = " + str(round(calculatedata[0].curvalue, calculatedata[0].target.digit))
                formula_chinese = "<div style=\"font-size:18px\"><span style=\"font-size:18px\"  class=\"label label-primary\"> " + \
                                  calculatedata[0].target.name + "</span>" + formula_chinese + "<br><br></div>"
            return HttpResponse(formula_chinese)


def reporting_recalculate(request):
    if request.user.is_authenticated():
        app = request.POST.get('app', '')
        cycletype = request.POST.get('cycletype', '')
        reporting_date = request.POST.get('reporting_date', '')
        operationtype = request.POST.get('operationtype', '')
        funid = request.POST.get('funid', '')
        work = None
        status = 1
        data = '计算成功。'
        try:
            funid = int(funid)
            fun = Fun.objects.get(id=funid)
            work = fun.work
        except:
            pass

        try:
            app = int(app)
            reporting_date = getreporting_date(reporting_date, cycletype)
        except:
            return HttpResponse(0)

        guid = uuid.uuid1()
        cur_target = Target.objects.exclude(state="9").filter(adminapp_id=app, cycletype=cycletype,
                                                              operationtype=operationtype, work=work)

        # 所有常数
        all_constant = Constant.objects.exclude(state="9").values()
        all_target = Target.objects.exclude(state="9")
        tableyear = str(reporting_date.year)
        EntryTable = getmodels("Entrydata", tableyear)
        MeterTable = getmodels("Meterdata", tableyear)
        ExtractTable = getmodels("Extractdata", tableyear)
        CalculateTable = getmodels("Calculatedata", tableyear)
        tableList = {"Entrydata": EntryTable, "Meterdata": MeterTable, "Extractdata": ExtractTable,
                     "Calculatedata": CalculateTable}

        for target in cur_target:
            if operationtype == "17":
                if target.calculateguid != str(guid):
                    try:
                        getcalculatedata(target, reporting_date, str(guid), all_constant, all_target, tableList)
                    except Exception as e:
                        print(e)
                        status = 0
                        data = '计算失败：{e}'.format(e=e)
                        break

        return JsonResponse({
            'status': status,
            'data': data
        })


def reporting_reextract(request):
    if request.user.is_authenticated():
        app = request.POST.get('app', '')
        cycletype = request.POST.get('cycletype', '')
        reporting_date = request.POST.get('reporting_date', '')
        operationtype = request.POST.get('operationtype', '')
        funid = request.POST.get('funid', '')
        work = None
        try:
            funid = int(funid)
            fun = Fun.objects.get(id=funid)
            work = fun.work
        except:
            pass

        try:
            app = int(app)
            reporting_date = getreporting_date(reporting_date, cycletype)
        except:
            return HttpResponse(0)

        guid = uuid.uuid1()
        all_target = Target.objects.exclude(state="9").filter(adminapp_id=app, cycletype=cycletype,
                                                              operationtype=operationtype, work=work)
        tableyear = str(reporting_date.year)

        EntryTable = getmodels("Entrydata", tableyear)
        MeterTable = getmodels("Meterdata", tableyear)
        ExtractTable = getmodels("Extractdata", tableyear)
        CalculateTable = getmodels("Calculatedata", tableyear)
        tableList = {"Entrydata": EntryTable, "Meterdata": MeterTable, "Extractdata": ExtractTable,
                     "Calculatedata": CalculateTable}

        for target in all_target:
            # 根据指标周期修改reporting_date
            a_cycle_aft_date = get_a_cycle_aft(reporting_date, cycletype)
            if operationtype == "16":
                extractdata = getmodels("Extractdata", str(reporting_date.year)).objects.exclude(state="9").filter(
                    target_id=target.id).filter(datadate=reporting_date)
                if len(extractdata) > 0:
                    extractdata = extractdata[0]
                    tablename = ""
                    try:
                        tablename = target.storage.tablename
                    except:
                        pass

                    rows = []
                    if tablename:
                        try:
                            with connection.cursor() as cursor:
                                reporting_date_stf = reporting_date.strftime("%Y-%m-%d %H:%M:%S")
                                strsql = "SELECT curvalue FROM {tablename} WHERE target_id='{target_id}' AND datadate='{datadate}' ORDER BY id DESC".format(
                                    tablename=tablename, target_id=target.id, datadate=reporting_date_stf
                                )
                                cursor.execute(strsql)
                                rows = cursor.fetchall()
                            connection.close()
                        except Exception as e:
                            pass
                        if len(rows) > 0:
                            try:
                                if target.is_repeat == '2':
                                    rownum = 0
                                    rowvalue = 0
                                    for row in rows:
                                        if row[0] is not None:
                                            rowvalue += row[0]
                                            rownum += 1
                                    extractdata.curvalue = rowvalue / rownum
                                else:
                                    extractdata.curvalue = rows[0][0]
                                extractdata.curvalue = decimal.Decimal(
                                    float(extractdata.curvalue) * float(target.magnification))
                                extractdata.curvalue = round(extractdata.curvalue, target.digit)
                            except:
                                pass
                    if not rows or not target.cycle:  # 没取到数据 或者 没有取数周期，根据数据源实时取
                        ret = Extract.getDataFromSource(target, a_cycle_aft_date)
                        result_list = ret["result"]
                        if result_list:
                            try:
                                if target.is_repeat == '2':
                                    rownum = 0
                                    rowvalue = 0
                                    for row in result_list:
                                        if row[0] is not None:
                                            rowvalue += row[0]
                                            rownum += 1
                                    extractdata.curvalue = rowvalue / rownum
                                else:
                                    extractdata.curvalue = result_list[0][0]
                                extractdata.curvalue = decimal.Decimal(
                                    float(extractdata.curvalue) * float(target.magnification))
                                extractdata.curvalue = round(extractdata.curvalue, target.digit)
                            except Exception as e:
                                print(e)

                    if target.cumulative in ['1', '2', '3', '4']:
                        cumulative = getcumulative(tableList, target, reporting_date, extractdata.curvalue)
                        extractdata.cumulativemonth = cumulative["cumulativemonth"]
                        extractdata.cumulativequarter = cumulative["cumulativequarter"]
                        extractdata.cumulativehalfyear = cumulative["cumulativehalfyear"]
                        extractdata.cumulativeyear = cumulative["cumulativeyear"]
                    extractdata.save()
        return HttpResponse(1)


def reporting_new(request):
    if request.user.is_authenticated():
        app = request.POST.get('app', '')
        cycletype = request.POST.get('cycletype', '')
        reporting_date = request.POST.get('reporting_date', '')
        operationtype = request.POST.get('operationtype', '')
        funid = request.POST.get('funid', '')
        work = None
        status = 1
        data = '新增成功。'

        try:
            funid = int(funid)
            fun = Fun.objects.get(id=funid)
            work = fun.work
        except:
            pass

        try:
            app = int(app)
            reporting_date = getreporting_date(reporting_date, cycletype)
        except:
            status = 0
            data = '应用不存在。'
        else:
            # 生成本次计算guid
            # 数据库中与本次guid不同的指标才参数计算
            guid = uuid.uuid1()
            cur_target = Target.objects.exclude(state="9").filter(
                adminapp_id=app, cycletype=cycletype, operationtype=operationtype, work=work
            ).order_by("sort")

            # 所有常数
            all_constant = Constant.objects.exclude(state="9").values()
            all_target = Target.objects.exclude(state="9")
            tableyear = str(reporting_date.year)

            EntryTable = getmodels("Entrydata", tableyear)
            MeterTable = getmodels("Meterdata", tableyear)
            ExtractTable = getmodels("Extractdata", tableyear)
            CalculateTable = getmodels("Calculatedata", tableyear)
            tableList = {"Entrydata": EntryTable, "Meterdata": MeterTable, "Extractdata": ExtractTable,
                         "Calculatedata": CalculateTable}

            for target in cur_target:
                # 根据指标周期修改reporting_date
                a_cycle_aft_date = get_a_cycle_aft(reporting_date, cycletype)
                # 电表走字
                if operationtype == "1":

                    all_meterdata = getmodels("Meterdata", str((reporting_date + datetime.timedelta(
                        days=-1)).year)).objects.exclude(state="9").filter(target=target,
                                                                           datadate=reporting_date + datetime.timedelta(
                                                                               days=-1))
                    meterdata = getmodels("Meterdata", str(reporting_date.year))()
                    if len(all_meterdata) > 0:
                        meterdata.zerodata = all_meterdata[0].twentyfourdata
                    else:
                        meterdata.zerodata = 0
                    meterdata.twentyfourdata = meterdata.zerodata

                    tablename = ""
                    try:
                        tablename = target.storage.tablename
                    except:
                        pass
                    # if tablename != "":
                    rows = []
                    if tablename:
                        try:
                            with connection.cursor() as cursor:
                                reporting_date_stf = reporting_date.strftime("%Y-%m-%d %H:%M:%S")
                                strsql = "SELECT curvalue FROM {tablename} WHERE target_id='{target_id}' AND datadate='{datadate}' ORDER BY id DESC".format(
                                    tablename=tablename, target_id=target.id, datadate=reporting_date_stf
                                )
                                cursor.execute(strsql)
                                rows = cursor.fetchall()
                        finally:
                            connection.close()

                    if len(rows) > 0:
                        try:
                            meterdata.twentyfourdata = rows[0][0]
                        except:
                            pass
                    if not rows or not target.cycle:  # 没取到数据 或者 没有取数周期，根据数据源实时取
                        ret = Extract.getDataFromSource(target, a_cycle_aft_date)
                        result_list = ret["result"]
                        if result_list:
                            try:
                                meterdata.twentyfourdata = result_list[0][0]
                            except:
                                pass

                    meterdata.target = target
                    meterdata.datadate = reporting_date
                    meterdata.metervalue = decimal.Decimal(meterdata.twentyfourdata) - decimal.Decimal(
                        meterdata.zerodata)
                    meterdata.curvalue = decimal.Decimal(meterdata.metervalue) * decimal.Decimal(target.magnification)
                    meterdata.curvalue = round(meterdata.curvalue, target.digit)
                    if target.cumulative in ['1', '2', '3', '4']:
                        cumulative = getcumulative(tableList, target, reporting_date, meterdata.curvalue)
                        meterdata.cumulativemonth = cumulative["cumulativemonth"]
                        meterdata.cumulativequarter = cumulative["cumulativequarter"]
                        meterdata.cumulativehalfyear = cumulative["cumulativehalfyear"]
                        meterdata.cumulativeyear = cumulative["cumulativeyear"]
                    meterdata.save()
                # 录入
                if operationtype == "15":
                    entrydata = getmodels("Entrydata", str(reporting_date.year))()
                    entrydata.target = target
                    entrydata.datadate = reporting_date
                    entrydata.curvalue = 0
                    if target.cumulative in ['1', '2', '3', '4']:
                        cumulative = getcumulative(tableList, target, reporting_date, entrydata.curvalue)
                        entrydata.cumulativemonth = cumulative["cumulativemonth"]
                        entrydata.cumulativequarter = cumulative["cumulativequarter"]
                        entrydata.cumulativehalfyear = cumulative["cumulativehalfyear"]
                        entrydata.cumulativeyear = cumulative["cumulativeyear"]
                    entrydata.save()
                # 提取
                if operationtype == "16":
                    extractdata = getmodels("Extractdata", str(reporting_date.year))()
                    extractdata.target = target
                    extractdata.datadate = reporting_date
                    extractdata.curvalue = -9999

                    tablename = ""
                    try:
                        tablename = target.storage.tablename
                    except:
                        pass

                    rows = []
                    if tablename:
                        try:
                            cursor = connection.cursor()
                            with connection.cursor() as cursor:
                                reporting_date_stf = reporting_date.strftime("%Y-%m-%d %H:%M:%S")
                                strsql = "SELECT curvalue FROM {tablename} WHERE target_id='{target_id}' AND datadate='{datadate}' ORDER BY id DESC".format(
                                    tablename=tablename, target_id=target.id, datadate=reporting_date_stf
                                )
                                cursor.execute(strsql)
                                rows = cursor.fetchall()
                            connection.close()
                        except Exception as e:
                            pass
                    if len(rows) > 0:
                        try:
                            if target.is_repeat == '2':
                                rownum = 0
                                rowvalue = 0
                                for row in rows:
                                    if row[0] is not None:
                                        rowvalue += row[0]
                                        rownum += 1
                                extractdata.curvalue = rowvalue / rownum
                            else:
                                extractdata.curvalue = rows[0][0]
                            extractdata.curvalue = decimal.Decimal(
                                float(extractdata.curvalue) * float(target.magnification))
                            extractdata.curvalue = round(extractdata.curvalue, target.digit)
                        except:
                            pass
                    if not rows or not target.cycle:  # 没取到数据 或者 没有取数周期，根据数据源实时取
                        ret = Extract.getDataFromSource(target, a_cycle_aft_date)
                        result_list = ret["result"]
                        if result_list:
                            try:
                                if target.is_repeat == '2':
                                    rownum = 0
                                    rowvalue = 0
                                    for row in result_list:
                                        if row[0] is not None:
                                            rowvalue += row[0]
                                            rownum += 1
                                    extractdata.curvalue = rowvalue / rownum
                                else:
                                    extractdata.curvalue = result_list[0][0]
                                extractdata.curvalue = decimal.Decimal(
                                    float(extractdata.curvalue) * float(target.magnification))
                                extractdata.curvalue = round(extractdata.curvalue, target.digit)
                            except Exception as e:
                                print(e)

                    if target.cumulative in ['1', '2', '3', '4']:
                        cumulative = getcumulative(tableList, target, reporting_date, extractdata.curvalue)
                        extractdata.cumulativemonth = cumulative["cumulativemonth"]
                        extractdata.cumulativequarter = cumulative["cumulativequarter"]
                        extractdata.cumulativehalfyear = cumulative["cumulativehalfyear"]
                        extractdata.cumulativeyear = cumulative["cumulativeyear"]
                    extractdata.save()
                # 计算
                if operationtype == "17":
                    # 为减少重复计算，判断指标calculate，如果指标calculate等于本次计算guid，则说明该指标在本次计算中以计算过
                    if target.calculateguid != str(guid):
                        try:
                            getcalculatedata(target, reporting_date, str(guid), all_constant, all_target, tableList)
                        except Exception as e:
                            print(e)
                            status = 0
                            data = '计算失败：{e}'.format(e=e)
                            import traceback
                            traceback.print_exc()
                            break

        return JsonResponse({
            'status': status,
            'data': data
        })


def reporting_del(request):
    if request.user.is_authenticated():
        result = {
            'status': 1,
            'data': '删除成功。'
        }
        app = request.POST.get('app', '')
        cycletype = request.POST.get('cycletype', '')
        reporting_date = request.POST.get('reporting_date', '')
        operationtype = request.POST.get('operationtype', '')
        funid = request.POST.get('funid', '')
        work = None
        user_id = request.user.id
        try:
            funid = int(funid)
            fun = Fun.objects.get(id=funid)
            work = fun.work
            app = int(app)
        except:
            result['status'] = 0
            result['data'] = '网络异常。'
        else:
            try:
                reporting_date = getreporting_date(reporting_date, cycletype)
            except:
                result['status'] = 0
                result['data'] = '报表时间处理异常。'
            else:
                all_data = []
                if operationtype == "1":
                    all_data = getmodels("Meterdata", str(reporting_date.year)).objects.exclude(state="9").filter(
                        target__adminapp_id=app, target__cycletype=cycletype,
                        target__work=work,
                        datadate=reporting_date)
                if operationtype == "15":
                    all_data = getmodels("Entrydata", str(reporting_date.year)).objects.exclude(state="9").filter(
                        target__adminapp_id=app, target__cycletype=cycletype,
                        target__work=work,
                        datadate=reporting_date)
                if operationtype == "16":
                    all_data = getmodels("Extractdata", str(reporting_date.year)).objects.exclude(state="9").filter(
                        target__adminapp_id=app,
                        target__cycletype=cycletype,
                        target__work=work,
                        datadate=reporting_date)
                if operationtype == "17":
                    all_data = getmodels("Calculatedata", str(reporting_date.year)).objects.exclude(state="9").filter(
                        target__adminapp_id=app,
                        target__cycletype=cycletype,
                        target__work=work,
                        datadate=reporting_date)

                if all_data:
                    try:
                        all_data.update(**{'state': '9', 'releasestate': '0'})
                    except Exception as e:
                        JsonResponse({
                            'status': 0,
                            'data': '删除失败。'
                        })
                    else:
                        ReportingLog.objects.create(**{
                            'write_time': datetime.datetime.now(),
                            'datadate': reporting_date,
                            'cycletype': cycletype,
                            'operationtype': operationtype,
                            'adminapp_id': app,
                            'work': work,
                            'user_id': user_id,
                            'type': 'del',
                        })

        return JsonResponse(result)


def reporting_release(request):
    if request.user.is_authenticated():
        result = {
            'status': 1,
            'data': '发布成功。'
        }
        app = request.POST.get('app', '')
        savedata = request.POST.get('savedata')
        savedata = json.loads(savedata)
        cycletype = request.POST.get('cycletype', '')
        reporting_date = request.POST.get('reporting_date', '')
        funid = request.POST.get('funid', '')
        work = None
        user_id = request.user.id

        try:
            funid = int(funid)
            fun = Fun.objects.get(id=funid)
            work = fun.work
            app = int(app)
        except Exception as e:
            print(e)
            result['status'] = 0
            result['data'] = '网络异常。'
        else:
            try:
                reporting_date = getreporting_date(reporting_date, cycletype)
            except Exception as e:
                result['status'] = 0
                result['data'] = '报表时间处理异常。'
            else:
                # 分别存入数据库
                savedata1 = savedata['1']
                savedata15 = savedata['15']
                savedata16 = savedata['16']
                savedata17 = savedata['17']

                # 发布
                error_info = ''

                try:
                    getmodels("Meterdata", str(reporting_date.year)).objects.exclude(state="9").filter(
                        id__in=[int(x['id']) for x in savedata1]).update(releasestate='1')
                except Exception as e:
                    error_info += '电表走字指标数据,'
                    result['status'] = 0
                try:
                    getmodels("Entrydata", str(reporting_date.year)).objects.exclude(state="9").filter(
                        id__in=[int(x['id']) for x in savedata15]).update(releasestate='1')
                except Exception as e:
                    error_info += '数据录入指标数据,'
                    result['status'] = 0
                try:
                    getmodels("Extractdata", str(reporting_date.year)).objects.exclude(state="9").filter(
                        id__in=[int(x['id']) for x in savedata16]).update(releasestate='1')
                except Exception as e:
                    error_info += '数据提取指标数据,'
                    result['status'] = 0
                try:
                    getmodels("Calculatedata", str(reporting_date.year)).objects.exclude(state="9").filter(
                        id__in=[int(x['id']) for x in savedata17]).update(releasestate='1')
                except Exception as e:
                    error_info += '数据计算指标数据'
                    result['status'] = 0

                if result['status']:
                    ReportingLog.objects.create(**{
                        'write_time': datetime.datetime.now(),
                        'datadate': reporting_date,
                        'cycletype': cycletype,
                        'adminapp_id': app,
                        'work': work,
                        'user_id': user_id,
                        'type': 'release',
                    })
                else:
                    result['data'] = '{0}发布失败。'.format(error_info[:-1] if error_info.endswith(',') else error_info)

        return JsonResponse(result)


def reporting_save(request):
    if request.user.is_authenticated():
        ret = {
            'status': 1,
            'data': '保存成功。'
        }
        savedata = request.POST.get('savedata')
        operationtype = request.POST.get('operationtype')
        cycletype = request.POST.get('cycletype', '')
        savedata = json.loads(savedata)
        reporting_date = request.POST.get('reporting_date', '')
        try:
            reporting_date = getreporting_date(reporting_date, cycletype)
        except:
            return JsonResponse({
                'status': 0,
                'data': '日期处理异常。'
            })

        # add
        tableyear = str(reporting_date.year)

        EntryTable = getmodels("Entrydata", tableyear)
        MeterTable = getmodels("Meterdata", tableyear)
        ExtractTable = getmodels("Extractdata", tableyear)
        CalculateTable = getmodels("Calculatedata", tableyear)
        tableList = {"Entrydata": EntryTable, "Meterdata": MeterTable, "Extractdata": ExtractTable,
                     "Calculatedata": CalculateTable}

        save_query_data = []
        meterchangedata = []
        # 循环前执行所有查询,所有需要存储的键值存储在{}中,直接执行queryset(id=?).update(**kwargs)
        # 相比get(),save(),减少查询的操作,直接更新
        if operationtype == "1":
            save_query_data = getmodels("Meterdata", str(reporting_date.year)).objects.exclude(state="9").values(
                'zerodata', 'twentyfourdata', 'metervalue', 'target__magnification',
                'curvalue', 'target__digit', 'target__datatype', 'curvaluedate', 'curvaluetext', 'cumulativemonth',
                'cumulativequarter',
                'cumulativehalfyear', 'cumulativeyear', 'id'
            )
            meterchangedata = Meterchangedata.objects.exclude(state="9").values()
        if operationtype == "15":
            save_query_data = getmodels("Entrydata", str(reporting_date.year)).objects.exclude(state="9").values(
                'curvalue', 'target__digit', 'target__datatype', 'curvaluedate', 'curvaluetext', 'cumulativemonth',
                'cumulativequarter',
                'cumulativehalfyear', 'cumulativeyear', 'id'
            )
        if operationtype == "16":
            save_query_data = getmodels("Extractdata", str(reporting_date.year)).objects.exclude(state="9").values(
                'curvalue', 'target__digit', 'target__datatype', 'curvaluedate', 'curvaluetext', 'cumulativemonth',
                'cumulativequarter',
                'cumulativehalfyear', 'cumulativeyear', 'id'
            )
        if operationtype == "17":
            save_query_data = getmodels("Calculatedata", str(reporting_date.year)).objects.exclude(state="9").values(
                'curvalue', 'target__digit', 'target__datatype', 'curvaluedate', 'curvaluetext', 'cumulativemonth',
                'cumulativequarter',
                'cumulativehalfyear', 'cumulativeyear', 'id'
            )

        for curdata in savedata:
            result = dict()

            # save to dict
            single_save_query_data = {}
            for sqd in save_query_data:
                if sqd['id'] == curdata['id']:
                    single_save_query_data = sqd
                    break
            if single_save_query_data:
                if single_save_query_data['target__datatype'] == 'numbervalue':
                    try:
                        result['curvalue'] = float(curdata["curvalue"])
                        result['curvalue'] = decimal.Decimal(str(curdata['curvalue'])).quantize(
                            decimal.Decimal(Digit(curdata['target__digit'])),
                            rounding=decimal.ROUND_HALF_UP)
                    except Exception as e:
                        pass
                if single_save_query_data['target__datatype'] == 'date':
                    try:
                        result['curvaluedate'] = datetime.datetime.strptime(curdata["curvaluedate"],
                                                                            "%Y-%m-%d %H:%M:%S")
                    except Exception as e:
                        pass
                if single_save_query_data['target__datatype'] == 'text':
                    try:
                        result['curvaluetext'] = curdata["curvaluetext"]
                    except Exception as e:
                        pass
                try:
                    result['zerodata'] = curdata["zerodata"]
                except Exception as e:
                    pass
                try:
                    result['twentyfourdata'] = curdata["twentyfourdata"]
                except Exception as e:
                    pass
                try:
                    result['metervalue'] = curdata["metervalue"]
                except Exception as e:
                    pass
                try:
                    result['cumulativemonth'] = float(curdata["cumulativemonth"])
                    result['cumulativemonth'] = round(curdata['cumulativemonth'],
                                                      single_save_query_data['target__digit'])
                except Exception as e:
                    pass
                try:
                    result['cumulativequarter'] = float(curdata["cumulativequarter"])
                    result['cumulativequarter'] = round(curdata['cumulativequarter'],
                                                        single_save_query_data['target__digit'])
                except Exception as e:
                    pass
                try:
                    result['cumulativehalfyear'] = float(curdata["cumulativehalfyear"])
                    result['cumulativehalfyear'] = round(curdata['cumulativehalfyear'],
                                                         save_query_data['target__digit'])
                except Exception as e:
                    pass
                try:
                    result['cumulativeyear'] = float(curdata["cumulativeyear"])
                    result['cumulativeyear'] = round(curdata['cumulativeyear'], save_query_data['target__digit'])
                except Exception as e:
                    pass

                if operationtype == "1":
                    getmodels("Meterdata", str(reporting_date.year)).objects.exclude(state="9").filter(
                        id=single_save_query_data['id']).update(**result)

                    # 电表走字换新表
                    if curdata["finalvalue"]:
                        # 倍率发生变化后修改
                        try:
                            newmagnification = float(curdata["magnification"])
                            if single_save_query_data['target__magnification'] != newmagnification:
                                try:
                                    tmp_metedata = getmodels("Meterdata", str(reporting_date.year)).objects.exclude(
                                        state="9").get(id=single_save_query_data['id'])
                                except Exception as e:
                                    pass
                                else:
                                    if tmp_metedata.target:
                                        tmp_metedata.target.magnification = newmagnification
                                        tmp_metedata.target.save()
                        except:
                            pass

                        meterchange_result = dict()

                        reporting_date = datetime.datetime.strptime(curdata["reporting_date"], "%Y-%m-%d")
                        try:
                            meterchange_result['datadate'] = reporting_date
                        except:
                            pass
                        try:
                            meterchange_result['meterdata'] = single_save_query_data['id']
                        except:
                            pass
                        try:
                            # meterchange_result['oldtable_zerodata'] = float(curdata["oldtable_zerodata"])
                            meterchange_result['oldtable_zerodata'] = decimal.Decimal(
                                str(float(curdata["oldtable_zerodata"])))
                        except:
                            pass
                        try:
                            # meterchange_result['oldtable_twentyfourdata'] = float(curdata["oldtable_twentyfourdata"])
                            meterchange_result['oldtable_twentyfourdata'] = decimal.Decimal(
                                str(float(curdata["oldtable_twentyfourdata"])))
                        except:
                            pass
                        try:
                            # meterchange_result['oldtable_value'] = float(curdata["oldtable_value"])
                            meterchange_result['oldtable_value'] = decimal.Decimal(
                                str(float(curdata["oldtable_value"])))
                        except:
                            pass
                        try:
                            # meterchange_result['oldtable_magnification'] = float(curdata["oldtable_magnification"])
                            meterchange_result['oldtable_magnification'] = decimal.Decimal(
                                str(float(curdata["oldtable_magnification"])))
                        except:
                            pass
                        try:
                            # meterchange_result['oldtable_finalvalue'] = float(curdata["oldtable_finalvalue"])
                            meterchange_result['oldtable_finalvalue'] = decimal.Decimal(
                                str(float(curdata["oldtable_finalvalue"])))
                        except:
                            pass
                        try:
                            # meterchange_result['newtable_zerodata'] = float(curdata["newtable_zerodata"])
                            meterchange_result['newtable_zerodata'] = decimal.Decimal(
                                str(float(curdata["newtable_zerodata"])))
                        except:
                            pass
                        try:
                            # meterchange_result['newtable_twentyfourdata'] = float(curdata["newtable_twentyfourdata"])
                            meterchange_result['newtable_twentyfourdata'] = decimal.Decimal(
                                str(float(curdata["newtable_twentyfourdata"])))
                        except:
                            pass
                        try:
                            # meterchange_result['newtable_value'] = float(curdata["newtable_value"])
                            meterchange_result['newtable_value'] = decimal.Decimal(
                                str(float(curdata["newtable_value"])))
                        except:
                            pass
                        try:
                            # meterchange_result['newtable_magnification'] = float(curdata["newtable_magnification"])
                            meterchange_result['newtable_magnification'] = decimal.Decimal(
                                str(float(curdata["newtable_magnification"])))
                        except:
                            pass
                        try:
                            # meterchange_result['newtable_finalvalue'] = float(curdata["newtable_finalvalue"])
                            meterchange_result['newtable_finalvalue'] = decimal.Decimal(
                                str(float(curdata["newtable_finalvalue"])))
                        except:
                            pass
                        try:
                            # meterchange_result['finalvalue'] = float(curdata["finalvalue"])
                            meterchange_result['finalvalue'] = decimal.Decimal(str(float(curdata["finalvalue"])))
                        except:
                            pass

                        mcd = Meterchangedata.objects.exclude(state="9").filter(meterdata=single_save_query_data['id'])
                        if mcd.exists():
                            mcd.update(**meterchange_result)
                        else:
                            mcd.create(**meterchange_result)

                if operationtype == "15":
                    getmodels("Entrydata", str(reporting_date.year)).objects.exclude(state="9").filter(
                        id=single_save_query_data['id']).update(**result)
                if operationtype == "16":
                    getmodels("Extractdata", str(reporting_date.year)).objects.exclude(state="9").filter(
                        id=single_save_query_data['id']).update(**result)
                if operationtype == "17":
                    getmodels("Calculatedata", str(reporting_date.year)).objects.exclude(state="9").filter(
                        id=single_save_query_data['id']).update(**result)
                # 保存时，重新累计
                try:
                    target = Target.objects.get(id=int(curdata['target_id']))
                    if target.cumulative in ['1', '2', '3', '4']:
                        cumulative = getcumulative(tableList, target, reporting_date, decimal.Decimal(str(curdata["curvalue"])))
                        operation_type = target.operationtype
                        table_name = map_operation(operation_type)
                        table_model = getmodels(table_name, str(reporting_date.year))
                        td_data = table_model.objects.filter(target=target).filter(datadate=reporting_date).exclude(state="9").last()
                        td_data.cumulativemonth = cumulative["cumulativemonth"]
                        td_data.cumulativequarter = cumulative["cumulativequarter"]
                        td_data.cumulativehalfyear = cumulative["cumulativehalfyear"]
                        td_data.cumulativeyear = cumulative["cumulativeyear"]
                        td_data.save()
                except Exception as e:
                    print(e)
            else:
                pass

        return JsonResponse(ret)


def report_submit_index(request, funid):
    """
    报表上报
    """
    if request.user.is_authenticated():
        errors = []
        id = ""
        report_type_list = []
        report_type = ""
        adminapp = ""
        try:
            cur_fun = Fun.objects.filter(id=int(funid)).exclude(state='9')
            adminapp = cur_fun[0].app_id
        except:
            return HttpResponseRedirect("/index")

        # 下拉框选项
        # 查看该应用有报表的类型
        report_types = ReportModel.objects.exclude(state="9").order_by("sort").filter(app_id=adminapp).values(
            "report_type"
        )
        all_report_types = [rt["report_type"] for rt in report_types]

        c_dict_index_1 = DictIndex.objects.filter(
            id=7).exclude(state='9')
        if c_dict_index_1.exists():
            c_dict_index_1 = c_dict_index_1[0]
            dict_list1 = c_dict_index_1.dictlist_set.exclude(state="9")
            for i in dict_list1:
                if str(i.id) in all_report_types:
                    report_type_list.append({
                        "report_name": i.name,
                        "report_type_id": i.id,
                    })

                    if not report_type:
                        report_type = i.id
        all_app = App.objects.exclude(state="9")
        all_app_list = []
        for app in all_app:
            all_app_list.append({
                "app_id": app.id,
                "app_name": app.name,
            })

        # datetimepicker
        date1 = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(
            days=-1)
        date2 = (datetime.datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(
            days=-1)).replace(day=1)

        date3 = ""
        seasondate = ""
        now = datetime.datetime.now()
        month = (now.month - 1) - (now.month - 1) % 3 + 1
        now = (datetime.datetime.now().replace(month=month, day=1, hour=0, minute=0, second=0,
                                               microsecond=0) + datetime.timedelta(days=-1))
        year = now.strftime("%Y")
        if now.month in (1, 2, 3):
            season = '第1季度'
            seasondate = year + '-' + season
            date3 = year + '-' + "03-31"
        if now.month in (4, 5, 6):
            season = '第2季度'
            seasondate = year + '-' + season
            date3 = year + '-' + "06-30"
        if now.month in (7, 8, 9):
            season = '第3季度'
            seasondate = year + '-' + season
            date3 = year + '-' + "09-30"
        if now.month in (10, 11, 12):
            season = '第4季度'
            seasondate = year + '-' + season
            date3 = year + '-' + "12-31"

        date4 = ""
        yeardate = ""
        now = datetime.datetime.now()
        month = (now.month - 1) - (now.month - 1) % 6 + 1
        now = (datetime.datetime.now().replace(month=month, day=1, hour=0, minute=0, second=0,
                                               microsecond=0) + datetime.timedelta(days=-1))
        year = now.strftime("%Y")
        if now.month in (1, 2, 3, 4, 5, 6):
            season = '上半年'
            yeardate = year + '-' + season
            date4 = year + '-' + "06-30"
        if now.month in (7, 8, 9, 10, 11, 12):
            season = '下半年'
            yeardate = year + '-' + season
            date4 = year + '-' + "12-31"

        date5 = (datetime.datetime.now().replace(month=1, day=1, hour=0, minute=0, second=0,
                                                 microsecond=0) + datetime.timedelta(days=-1)).replace(month=1, day=1)

        temp_dict = {
            "22": date1.strftime("%Y-%m-%d"),
            "23": date2.strftime("%Y-%m"),
            "24": date3,
            "25": date4,
            "26": date5.strftime("%Y"),
        }

        return render(request, 'report_submit.html',
                      {'username': request.user.userinfo.fullname,
                       "selected_report_type": report_type,
                       "report_type_list": report_type_list,
                       "all_app_list": all_app_list,
                       "errors": errors,
                       "id": id,
                       "date": json.dumps(temp_dict),
                       "dateday": date1.strftime("%Y-%m-%d"),
                       "seasondate": seasondate,
                       "yeardate": yeardate,
                       "adminapp": adminapp,
                       "funid": funid,
                       "pagefuns": getpagefuns(funid)})
    else:
        return HttpResponseRedirect("/login")


def report_submit_data(request):
    if request.user.is_authenticated():
        result = []
        search_app = request.GET.get('search_app', '')
        search_date = request.GET.get('search_date', '')
        search_report_type = request.GET.get('search_report_type', '')

        # 时间的过滤
        if search_date:
            if search_report_type == "22":
                search_date = datetime.datetime.strptime(search_date, "%Y-%m-%d")
            elif search_report_type == "23":
                search_date = datetime.datetime.strptime(search_date, "%Y-%m")
                year = search_date.year
                month = search_date.month
                a, b = calendar.monthrange(year, month)
                search_date = datetime.datetime(year=year, month=month, day=b)
            elif search_report_type == "24":
                search_date = search_date
            elif search_report_type == "25":
                search_date = search_date
            elif search_report_type == "26":
                search_date = datetime.datetime.strptime(search_date, "%Y")
                search_date = search_date.replace(month=12, day=31)
        else:
            pass

        all_report = ReportModel.objects.exclude(state="9").order_by("sort").filter(report_type=search_report_type)
        curadminapp = App.objects.get(id=int(search_app))
        all_report = all_report.filter(app=curadminapp)

        # 报表服务器地址
        rs = ReportServer.objects.first()
        report_server = rs.report_server if rs else ''

        for report in all_report:
            # 报表类型
            report_type = report.report_type
            report_time = ''
            try:
                report_type_dict_list = DictList.objects.filter(id=int(report.report_type))
                if report_type_dict_list.exists():
                    report_type_dict_list = report_type_dict_list[0]
                    report_type = report_type_dict_list.name
            except:
                pass

            report_info_list = []

            current_report_info_set = report.reportinfo_set.exclude(state="9")
            if current_report_info_set.exists():
                for report_info in current_report_info_set:
                    report_info_list.append({
                        "report_info_name": report_info.name,
                        "report_info_value": report_info.default_value,
                        "report_info_id": int(report_info.id),
                    })

            # state判断  report_time/state==1
            report_submit_1 = report.reportsubmit_set.exclude(state="9").filter(report_time=search_date, state="1")
            report_submit_0 = report.reportsubmit_set.exclude(state="9").filter(report_time=search_date, state="0")

            if report_submit_1.exists():
                state = "已发布"
                person = report_submit_1[0].person
                write_time = report_submit_1[0].write_time.strftime('%Y-%m-%d')

                c_report_time = report_submit_1[0].report_time
                # 年 月 日  2019-01-01
                if c_report_time:
                    if report_type == "年报":
                        report_time = c_report_time.strftime('%Y')
                    if report_type in ["半年报", "季报", "日报"]:
                        report_time = c_report_time.strftime('%Y-%m-%d')
                    if report_type == "月报":
                        report_time = c_report_time.strftime('%Y-%m')
                c_report_info_list = []
                current_report_submit_info_set = report_submit_1[0].reportsubmitinfo_set.exclude(state="9")
                for report_submit_info in current_report_submit_info_set:
                    c_report_info_list.append({
                        "report_info_name": report_submit_info.name,
                        "report_info_value": report_submit_info.value,
                        "report_info_id": int(report_submit_info.id),
                    })
                report_info_list = c_report_info_list
            elif report_submit_0.exists():
                state = "未发布"
                person = report_submit_0[0].person
                write_time = report_submit_0[0].write_time.strftime('%Y-%m-%d')
                c_report_time = report_submit_0[0].report_time
                if c_report_time:
                    if report_type == "年报":
                        report_time = c_report_time.strftime('%Y')
                    if report_type in ["半年报", "季报", "日报"]:
                        report_time = c_report_time.strftime('%Y-%m-%d')
                    if report_type == "月报":
                        report_time = c_report_time.strftime('%Y-%m')
                c_report_info_list = []
                current_report_submit_info_set = report_submit_0[0].reportsubmitinfo_set.exclude(state="9")
                for report_submit_info in current_report_submit_info_set:
                    c_report_info_list.append({
                        "report_info_name": report_submit_info.name,
                        "report_info_value": report_submit_info.value,
                        "report_info_id": int(report_submit_info.id),
                    })
                report_info_list = c_report_info_list
            else:
                state = "未创建"
                person = str(request.user.userinfo.fullname) if request.user.userinfo else ''
                write_time = datetime.datetime.now().strftime('%Y-%m-%d')
                report_time = ""

            result.append({
                "id": report.id,
                "name": report.name,
                "code": report.code,
                "file_name": report.file_name,
                "relative_file_name": report.app.code + '/' + report.file_name,
                "report_type": report_type,
                "report_type_id": int(report.report_type) if report.report_type else "",
                "app": report.app.name,
                "app_id": report.app.id,
                "report_type_num": report.report_type,
                "sort": report.sort,
                "report_info_list": report_info_list,
                "person": person,
                "write_time": write_time,
                "state": state,
                "report_time": report_time,
                "report_server": report_server
            })
        return JsonResponse({"data": result})


def report_submit_save(request):
    if request.user.is_authenticated():
        # 新增/修改报表模型
        if request.method == "POST":
            result = {}
            person = request.POST.get("person", "")
            write_time = request.POST.get("write_time", "")
            report_model = request.POST.get("report_model", "")
            app = request.POST.get("app", "")
            post_type = request.POST.get("post_type", "")
            report_time = request.POST.get("report_time", "")

            write_time = datetime.datetime.strptime(write_time, "%Y-%m-%d") if write_time else None
            length_tag = report_time.count("-")
            if length_tag == 0:
                report_time = datetime.datetime.strptime(report_time, "%Y") if report_time else None
                report_time = report_time.replace(month=12, day=31) if report_time else None
            elif length_tag == 1:
                report_time = datetime.datetime.strptime(report_time, "%Y-%m") if report_time else None
                a, b = calendar.monthrange(report_time.year, report_time.month) if report_time else None
                report_time = datetime.datetime(year=report_time.year, month=report_time.month,
                                                day=b) if report_time else None
            elif length_tag == 2:
                report_time = datetime.datetime.strptime(report_time, "%Y-%m-%d") if report_time else None
            else:
                result["res"] = "网络异常。"
                return JsonResponse(result)

            report_info_num = 0
            for key in request.POST.keys():
                if "report_info_" in key:
                    report_info_num += 1

            if report_model:
                report_model = int(report_model)

                current_report_submit = ReportSubmit.objects.exclude(state="9").filter(report_model_id=report_model,
                                                                                       report_time=report_time)
                # 新增
                if not current_report_submit.exists():
                    try:
                        report_submit_add = ReportSubmit()
                        report_submit_add.report_model_id = report_model
                        report_submit_add.app_id = app
                        report_submit_add.person = person
                        report_submit_add.state = "0"
                        report_submit_add.write_time = write_time
                        report_submit_add.report_time = report_time
                        if post_type == "submit":
                            report_submit_add.state = "1"
                        report_submit_add.save()

                        # report_info
                        if report_info_num:
                            range_num = int(report_info_num / 3)
                            for i in range(0, range_num):
                                report_submit_info = ReportSubmitInfo()
                                report_info_name = request.POST.get(
                                    "report_info_name_%d" % (i + 1), "")
                                report_info_default_value = request.POST.get(
                                    "report_info_value_%d" % (i + 1), "")
                                if report_info_name:
                                    report_submit_info.name = report_info_name
                                    report_submit_info.value = report_info_default_value
                                    report_submit_info.report_submit = report_submit_add
                                    report_submit_info.save()
                        result["res"] = "保存成功。"
                    except Exception as e:
                        result["res"] = "网络异常。"
                        return JsonResponse(result)
                # 修改
                else:
                    current_report_submit = current_report_submit[0]
                    try:
                        if post_type == "submit":
                            current_report_submit.state = "1"
                        current_report_submit.person = person
                        current_report_submit.write_time = write_time
                        current_report_submit.report_time = report_time
                        current_report_submit.save()
                        if report_info_num:
                            range_num = int(report_info_num / 3)
                            for i in range(0, range_num):
                                report_info_id = request.POST.get(
                                    "report_info_id_%d" % (i + 1), "")
                                report_info_name = request.POST.get(
                                    "report_info_name_%d" % (i + 1), "")
                                report_info_value = request.POST.get(
                                    "report_info_value_%d" % (i + 1), "")
                                temp_report_submit_info = ReportSubmitInfo.objects.exclude(state="9").filter(
                                    id=int(report_info_id))
                                if temp_report_submit_info.exists():
                                    temp_report_submit_info = temp_report_submit_info[0]
                                    temp_report_submit_info.name = report_info_name
                                    temp_report_submit_info.value = report_info_value
                                    temp_report_submit_info.save()
                        result["res"] = "保存成功。"
                    except Exception as e:
                        result["res"] = "网络异常。"
                        return JsonResponse(result)
            else:
                result["res"] = "网络异常。"
            return JsonResponse(result)


def report_submit_del(request):
    if request.user.is_authenticated():
        if 'id' in request.POST:
            id = request.POST.get('id', '')
            report_time = request.POST.get("report_time", "")

            length_tag = report_time.count("-")
            if length_tag == 0:
                report_time = datetime.datetime.strptime(report_time, "%Y") if report_time else None
                report_time = report_time.replace(month=12, day=31) if report_time else None
            elif length_tag == 1:
                report_time = datetime.datetime.strptime(report_time, "%Y-%m") if report_time else None
                a, b = calendar.monthrange(report_time.year, report_time.month) if report_time else None
                report_time = datetime.datetime(year=report_time.year, month=report_time.month,
                                                day=b) if report_time else None
            elif length_tag == 2:
                report_time = datetime.datetime.strptime(report_time, "%Y-%m-%d") if report_time else None
            else:
                return HttpResponse(0)

            try:
                id = int(id)
            except:
                raise Http404()
            report = ReportModel.objects.filter(id=id)

            if report.exists():
                report = report[0]
                # 删除关联report_submit
                report_submit_set = report.reportsubmit_set.exclude(state="9").filter(report_time=report_time)
                if report_submit_set.exists():
                    for i in report_submit_set:
                        i.state = "9"
                        i.save()
                else:
                    # 未创建，不需要删除
                    return HttpResponse(2)

                return HttpResponse(1)
            else:
                return HttpResponse(0)
        else:
            return HttpResponse(0)


def getfun(myfunlist, fun):
    try:
        if (fun.pnode_id is not None):
            if fun not in myfunlist:
                childfun = {}
                if (fun.pnode_id != 1):
                    myfunlist = getfun(myfunlist, fun.pnode)
                myfunlist.append(fun)
    except:
        pass
    return myfunlist


def childfun(myfun, funid):
    mychildfun = []
    funs = myfun.children.order_by("sort").exclude(state="9")

    pisselected = False
    for fun in funs:
        if fun in funlist:
            isselected = False
            url = fun.url if fun.url else ""
            # if len(fun.app.all()) > 0:
            if fun.app:
                url = fun.url + str(fun.id) + "/" if fun.url else ""
            if str(fun.id) == funid:
                isselected = True
                pisselected = True
                mychildfun.append({
                    "id": fun.id, "name": fun.name, "url": url,
                    "icon": fun.icon, "isselected": isselected,
                    "child": [], "new_window": fun.if_new_wd,
                })
            else:
                returnfuns = childfun(fun, funid)
                mychildfun.append({
                    "id": fun.id, "name": fun.name, "url": url, "icon": fun.icon,
                    "isselected": returnfuns["isselected"], "child": returnfuns["fun"],
                    "new_window": fun.if_new_wd,
                })
                if returnfuns["isselected"]:
                    pisselected = returnfuns["isselected"]
    return {"fun": mychildfun, "isselected": pisselected}


def getpagefuns(funid, request=""):
    pagefuns = []
    mycurfun = {}
    message_task = []
    task_nums = 0

    for fun in funlist:
        if fun.pnode_id == 1:
            isselected = False
            url = fun.url if fun.url else ""
            if fun.app:
                url = fun.url + str(fun.id) + "/" if fun.url else ""
            if str(fun.id) == funid:
                isselected = True
                pagefuns.append({
                    "id": fun.id, "name": fun.name, "url": url,
                    "icon": fun.icon, "isselected": isselected,
                    "child": [], "new_window": fun.if_new_wd,
                })
            else:
                returnfuns = childfun(fun, funid)
                pagefuns.append({
                    "id": fun.id, "name": fun.name, "url": url, "icon": fun.icon,
                    "isselected": returnfuns["isselected"], "child": returnfuns["fun"],
                    "new_window": fun.if_new_wd,
                })

    curfun = Fun.objects.filter(id=int(funid))
    if len(curfun) > 0:
        myurl = curfun[0].url
        jsurl = curfun[0].url  # /falconstorswitch/24
        if myurl:
            myurl = myurl[:-1]
            jsurl = jsurl[1:-1]
            curjsurl = jsurl.split('/')
            jsurl = '/' + curjsurl[0]

        mycurfun = {
            "id": curfun[0].id, "name": curfun[0].name, "url": myurl, "jsurl": jsurl
        }

    return {"pagefuns": pagefuns, "curfun": mycurfun, "task_nums": task_nums}


def test(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        errors = []
        code = "DLZX_JYTJ_FDL_NJH"
        ret = get_target_data_recently(code)
        return render(request, 'test.html',
                      {'username': request.user.userinfo.fullname, "errors": errors})
    else:
        return HttpResponseRedirect("/login")


def custom_personal_fun_list(if_superuser, userinfo_id):
    funlist = []
    if if_superuser == 1:
        allfunlist = Fun.objects.all()
        for fun in allfunlist:
            funlist.append(fun)
    else:
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "select datacenter_fun.id from datacenter_group,datacenter_fun,datacenter_userinfo,datacenter_userinfo_group,datacenter_group_fun "
                    "where datacenter_group.id=datacenter_userinfo_group.group_id and datacenter_group.id=datacenter_group_fun.group_id and "
                    "datacenter_group_fun.fun_id=datacenter_fun.id and datacenter_userinfo.id=datacenter_userinfo_group.userinfo_id and userinfo_id= "
                    + str(userinfo_id) + " order by datacenter_fun.sort"
                )

                rows = cursor.fetchall()
                for row in rows:
                    try:
                        fun = Fun.objects.get(id=row[0])
                        funlist = getfun(funlist, fun)
                    except:
                        pass
        finally:
            connection.close()
    for index, value in enumerate(funlist):
        if value.sort is None:
            value.sort = 0
    funlist = sorted(funlist, key=lambda fun: fun.sort)
    return funlist


def index(request, funid):
    if request.user.is_authenticated():
        global funlist
        funlist = custom_personal_fun_list(request.user.is_superuser, request.user.userinfo.id)
        # 右上角消息任务
        return render(request, "index.html",
                      {'username': request.user.userinfo.fullname, "homepage": True,
                       "pagefuns": getpagefuns(funid, request),
                       })
    else:
        return HttpResponseRedirect("/login")


def login(request):
    """
    @param login?error=n
        n=1 用户不存在
        n=2 用户认证失败
    """
    error_tag = request.GET.get("error", "")
    error = ""
    try:
        error_tag = int(error_tag)
    except Exception:
        pass

    if error_tag == 1:
        error = "用户登录失败。"
    if error_tag == 2:
        error = "用户认证失败。"

    auth.logout(request)
    try:
        del request.session['ispuser']
        del request.session['isadmin']
    except KeyError:
        pass
    return render(request, 'login.html', locals())


@csrf_exempt
def ad_login(request):
    """
    @return login?error=n
        n=1 用户不存在
        n=2 用户认证失败
    """
    username = request.POST.get('username', '')
    password = request.POST.get('password', '')
    user = auth.authenticate(username=username, password=password)
    if user is not None and user.is_active:
        auth.login(request, user)
        if request.user.is_authenticated():
            request.session.set_expiry(0)
            usertype = user.userinfo.usertype
            if usertype == '1':
                request.session['ispuser'] = True
            else:
                request.session['ispuser'] = False
            request.session['isadmin'] = user.is_superuser
            return HttpResponseRedirect("/index")
        else:
            return HttpResponseRedirect('/login?error=2')
    else:
        return HttpResponseRedirect('/login?error=1')


def userlogin(request):
    if request.method == 'POST':
        result = ""
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        # 加入AD认证
        user = auth.authenticate(username=username, password=password)
        if user is not None and user.is_active:
            auth.login(request, user)
            myuserinfo = user.userinfo
            if myuserinfo.forgetpassword:
                myuserinfo.forgetpassword = ""
                myuserinfo.save()
            if request.user.is_authenticated():
                if myuserinfo.state == "0":
                    result = "success1"
                else:
                    result = "success"
                if (request.POST.get('remember', '') != '1'):
                    request.session.set_expiry(0)
                # myuser = User.objects.get(username=username)
                usertype = user.userinfo.usertype
                if usertype == '1':
                    request.session['ispuser'] = True
                else:
                    request.session['ispuser'] = False
                request.session['isadmin'] = user.is_superuser
            else:
                result = "登录失败，请于客服联系。"
        else:
            result = "用户名或密码不正确。"

    return HttpResponse(result)


def forgetPassword(request):
    if request.method == 'POST':
        result = ""
        email = request.POST.get('email', '')
        alluser = User.objects.filter(email=email)
        if (len(alluser) <= 0):
            result = u"邮箱" + email + u'不存在。'
        else:
            myuserinfo = alluser[0].userinfo
            url = str(uuid.uuid1())
            subject = u'密码重置'
            message = u'用户:' + alluser[0].username + u'您好。' \
                      + u"\n您在云灾备系统申请了密码重置，点击链接进入密码重置页面:" \
                      + u"http://127.0.0.1:8000/resetpassword/" + url
            send_mail(subject, message, settings.EMAIL_HOST_USER,
                      [alluser[0].email])
            myuserinfo.forgetpassword = url
            myuserinfo.save()
            result = "邮件发送成功，请注意查收。"
        return HttpResponse(result)


def resetpassword(request, offset):
    myuserinfo = UserInfo.objects.filter(forgetpassword=offset)
    if len(myuserinfo) > 0:
        myusername = myuserinfo[0].user.username
        return render(request, 'reset.html', {"myusername": myusername})
    else:
        return render(request, 'reset.html', {"error": True})


def reset(request):
    if request.method == 'POST':
        result = ""
        myusername = request.POST.get('username', '')
        password = request.POST.get('password', '')

        alluser = User.objects.filter(username=myusername)
        if (len(alluser) > 0):
            alluser[0].set_password(password)
            alluser[0].save()
            myuserinfo = alluser[0].userinfo
            myuserinfo.forgetpassword = ""
            myuserinfo.save()
            if myuserinfo.state == "0":
                result = "success1"
            else:
                result = "success"
            auth.logout(request)
            user = auth.authenticate(username=myusername, password=password)
            if user is not None and user.is_active:
                auth.login(request, user)
                usertype = myuserinfo.type
                if usertype == '1':
                    request.session['ispuser'] = True
                else:
                    request.session['ispuser'] = False
                request.session['isadmin'] = alluser[0].is_superuser
        else:
            result = "用户不存在。"
        return HttpResponse(result)


def password(request):
    if request.user.is_authenticated():
        return render(request, 'password.html', {"myusername": request.user.username})
    else:
        return HttpResponseRedirect("/login")


def userpassword(request):
    if request.method == 'POST':
        result = ""
        username = request.POST.get('username', '')
        oldpassword = request.POST.get('oldpassword', '')
        password = request.POST.get('password', '')
        user = auth.authenticate(username=username, password=oldpassword)
        if user is not None and user.is_active:
            alluser = User.objects.filter(username=username)
            if (len(alluser) > 0):
                alluser[0].set_password(password)
                alluser[0].save()
                myuserinfo = alluser[0].userinfo
                myuserinfo.forgetpassword = ""
                myuserinfo.save()
                result = "success"
                auth.logout(request)
                user = auth.authenticate(username=username, password=password)
                if user is not None and user.is_active:
                    auth.login(request, user)
                    usertype = myuserinfo.type
                    if usertype == '1':
                        request.session['ispuser'] = True
                    else:
                        request.session['ispuser'] = False
                    request.session['isadmin'] = alluser[0].is_superuser
            else:
                result = "用户异常，修改密码失败。"
        else:
            result = "旧密码输入错误，请重新输入。"

    return HttpResponse(result)


def get_fun_tree(parent, selectid, all_apps, all_nodes, all_works):
    nodes = []

    children = [child for child in all_nodes if child['pnode_id'] == parent['id']]
    for child in children:
        node = dict()
        node["text"] = child['name']
        node["id"] = child['id']
        node["type"] = child['funtype']
        # app应用
        # 当前节点的所有外键
        current_app_id = child['app_id']

        app_select_list = [{
            "app_name": "",
            "id": "",
            "app_state": "",
        }]
        for app in all_apps:
            works = [{
                'id': work['id'],
                'name': work['name']
            } for work in all_works if work['app_id'] == app['id']]

            app_select_list.append({
                "app_name": app['name'],
                "id": app['id'],
                "app_state": "selected" if app['id'] == current_app_id else "",
                "works": str(works),
            })

        selected_work = child['work_id']

        node["data"] = {
            "url": child['url'],
            "icon": child['icon'],
            "pname": parent['name'],
            "app_list": app_select_list,
            "app_div_show": True if child['funtype'] == "fun" else False,
            "selected_work": selected_work,
            "new_window": child["if_new_wd"],
        }
        node["children"] = get_fun_tree(child, selectid, all_apps, all_nodes, all_works)

        try:
            if int(selectid) == child['id']:
                node["state"] = {"selected": True}
        except:
            pass
        nodes.append(node)
    return nodes


def function(request, funid):
    if request.user.is_authenticated():
        try:
            errors = []
            title = "请选择功能"
            selectid = ""
            id = ""
            pid = ""
            pname = ""
            name = ""
            mytype = ""
            url = ""
            icon = ""
            app_list = []
            pre_app_select_list = []
            works_select_list = []
            hiddendiv = "hidden"
            app_hidden_div = ""

            visited_url_div = ""
            new_window_div = ""

            all_apps = App.objects.exclude(state="9").values()
            all_works = Work.objects.exclude(state='9').values('id', 'name', 'app_id')

            if request.method == 'POST':
                hiddendiv = ""
                id = request.POST.get('id')
                pid = request.POST.get('pid')
                pname = request.POST.get('pname')
                name = request.POST.get('name')
                mytype = request.POST.get('radio2')
                url = request.POST.get('url')
                icon = request.POST.get('icon')
                app = request.POST.get('app', '')
                works = request.POST.get('works', '')
                new_window = request.POST.get('new_window', '')
                try:
                    id = int(id)
                except:
                    raise Http404()
                try:
                    pid = int(pid)
                except:
                    raise Http404()
                if id == 0:
                    selectid = pid
                    title = "新建"
                else:
                    selectid = id
                    title = name

                try:
                    works = int(works)
                except:
                    pass

                if name.strip() == '':
                    errors.append('功能名称不能为空。')
                else:
                    try:
                        pfun = Fun.objects.get(id=pid)
                    except:
                        raise Http404()
                    try:
                        if id == 0:
                            sort = 1

                            try:
                                maxfun = Fun.objects.filter(
                                    pnode=pfun).latest('sort')
                                sort = maxfun.sort + 1
                                sort = maxfun.sort + 1
                            except:
                                pass
                            funsave = Fun()
                            funsave.pnode = pfun
                            funsave.name = name
                            funsave.funtype = mytype
                            funsave.url = url
                            funsave.icon = icon
                            funsave.sort = sort if sort else None
                            funsave.app_id = int(app) if app else None
                            funsave.work_id = works
                            funsave.if_new_wd = new_window
                            funsave.save()

                            title = name
                            id = funsave.id
                            selectid = id
                        else:
                            funsave = Fun.objects.get(id=id)
                            if funsave.funtype == "node" and mytype == "fun" and len(
                                    funsave.children.exclude(state="9")) > 0:
                                errors.append('节点下还有其他节点或功能，无法修改为功能。')
                            elif mytype == "node" and funsave.app:
                                errors.append('功能下有关联应用，无法修改为节点。')
                            else:
                                funsave.name = name
                                funsave.funtype = mytype
                                funsave.url = url
                                funsave.icon = icon
                                funsave.app_id = int(app) if app else None
                                funsave.work_id = works
                                funsave.if_new_wd = new_window
                                funsave.save()

                                title = name
                        # 保存成功后，重新刷新页面，重新构造app_select_list
                        for c_app in all_apps:
                            pre_app_select_list.append({
                                "app_name": c_app['name'],
                                "id": c_app['id'],
                                "app_state": "selected" if str(c_app['id']) == app else "",
                            })
                        # 保存成功后，重新构造 works_select_list
                        try:
                            select_app = App.objects.get(id=app)
                        except Exception as e:
                            pass
                        else:
                            works_list = select_app.work_set.exclude(state='9')
                            if works_list.exists():
                                for work in works_list:
                                    if work.id == works:
                                        # selected
                                        works_select_list.append({
                                            'id': work.id,
                                            'name': work.name,
                                            'selected': 'selected'
                                        })
                                    else:
                                        works_select_list.append({
                                            'id': work.id,
                                            'name': work.name,
                                            'selected': ''
                                        })

                        if mytype == "node":
                            app_hidden_div = "hidden"
                            visited_url_div = "hidden"
                            new_window_div = "hidden"
                        else:
                            app_hidden_div = ""
                            visited_url_div = ""
                            new_window_div = ""

                        # 功能节点修改后，更新funlist
                        global funlist
                        funlist = custom_personal_fun_list(request.user.is_superuser, request.user.userinfo.id)
                    except Exception as e:
                        print(e)
                        errors.append('保存失败。')
            treedata = []

            all_nodes = Fun.objects.exclude(state='9').order_by('sort').values()
            rootnodes = [node for node in all_nodes if node['pnode_id'] == None]

            for rootnode in rootnodes:
                root = dict()
                root["text"] = rootnode['name']
                root["id"] = rootnode['id']
                root["type"] = "node"

                # 当前节点的所有外键
                current_app_id = rootnode['app_id']

                app_select_list = [{
                    "app_name": "",
                    "id": "",
                    "app_state": "",
                }]
                for app in all_apps:
                    works = [{
                        'id': work['id'],
                        'name': work['name']
                    } for work in all_works if work['app_id'] == app['id']]

                    app_select_list.append({
                        "app_name": app['name'],
                        "id": app['id'],
                        "app_state": "selected" if app['id'] == current_app_id else "",
                        "works": str(works),
                    })

                selected_work = rootnode['work_id']

                root["data"] = {
                    "url": rootnode['url'],
                    "icon": rootnode['icon'],
                    "pname": "无",
                    "app_list": app_select_list,
                    "app_div_show": True if rootnode['funtype'] == "fun" else False,
                    "selected_work": selected_work,
                    "new_window": rootnode["if_new_wd"],
                }
                try:
                    if int(selectid) == rootnode['id']:
                        root["state"] = {"opened": True, "selected": True}
                    else:
                        root["state"] = {"opened": True}
                except:
                    root["state"] = {"opened": True}
                root["children"] = get_fun_tree(rootnode, selectid, all_apps, all_nodes, all_works)
                treedata.append(root)

            treedata = json.dumps(treedata)
            return render(request, 'function.html', {
                'username': request.user.userinfo.fullname, 'errors': errors, "id": id,
                "pid": pid, "pname": pname, "name": name, "url": url, "icon": icon, "title": title,
                "mytype": mytype, "hiddendiv": hiddendiv, "treedata": treedata,
                "works_select_list": works_select_list,
                "app_select_list": pre_app_select_list, "app_hidden_div": app_hidden_div,
                "pagefuns": getpagefuns(funid, request=request),
                "visited_url_div": visited_url_div,
                "new_window_div": new_window_div,
            })
        except Exception as e:
            print(e)
            return HttpResponseRedirect("/index")
    else:
        return HttpResponseRedirect("/login")


def fundel(request):
    if request.user.is_authenticated():
        if 'id' in request.POST:
            id = request.POST.get('id', '')
            try:
                id = int(id)
            except:
                raise Http404()
            allfun = Fun.objects.filter(id=id)
            if (len(allfun) > 0):
                sort = allfun[0].sort
                pfun = allfun[0].pnode
                allfun[0].delete()
                sortfuns = Fun.objects.filter(pnode=pfun).filter(sort__gt=sort)
                if len(sortfuns) > 0:
                    for sortfun in sortfuns:
                        try:
                            sortfun.sort = sortfun.sort - 1
                            sortfun.save()
                        except:
                            pass

                # 删除时更新右侧菜单
                global funlist

                funlist = custom_personal_fun_list(request.user.is_superuser, request.user.userinfo.id)
                return HttpResponse(1)
            else:
                return HttpResponse(0)


def funmove(request):
    if request.user.is_authenticated():
        if 'id' in request.POST:
            id = request.POST.get('id', '')
            parent = request.POST.get('parent', '')
            old_parent = request.POST.get('old_parent', '')
            position = request.POST.get('position', '')
            old_position = request.POST.get('old_position', '')
            try:
                id = int(id)
            except:
                raise Http404()
            try:
                parent = int(parent)
            except:
                raise Http404()
            try:
                position = int(position)
            except:
                raise Http404()
            try:
                parent = int(parent)
            except:
                raise Http404()
            try:
                old_position = int(old_position)
            except:
                raise Http404()

            oldpfun = Fun.objects.get(id=old_parent)
            oldsort = old_position + 1
            oldfuns = Fun.objects.filter(
                pnode=oldpfun).filter(sort__gt=oldsort)

            pfun = Fun.objects.get(id=parent)
            sort = position + 1
            funs = Fun.objects.filter(pnode=pfun).filter(
                sort__gte=sort).exclude(id=id)

            if pfun.funtype == "fun":
                return HttpResponse("类型")
            else:
                if (len(oldfuns) > 0):
                    for oldfun in oldfuns:
                        try:
                            oldfun.sort = oldfun.sort - 1
                            oldfun.save()
                        except:
                            pass

                if (len(funs) > 0):
                    for fun in funs:
                        try:
                            fun.sort = fun.sort + 1
                            fun.save()
                        except:
                            pass
                myfun = Fun.objects.get(id=id)
                try:
                    myfun.pnode = pfun
                    myfun.sort = sort
                    myfun.save()
                except:
                    pass
                if parent != old_parent:
                    return HttpResponse(pfun.name + "^" + str(pfun.id))
                else:
                    return HttpResponse("0")


def get_org_tree(parent, selectid, allgroup):
    nodes = []
    children = parent.children.order_by("sort").exclude(state="9")
    for child in children:
        node = {}
        node["text"] = child.fullname
        node["id"] = child.id
        node["type"] = child.usertype
        if child.usertype == "org":
            myallgroup = []
            for group in allgroup:
                myallgroup.append({"groupname": group.name, "id": group.id})
            node["data"] = {"remark": child.remark,
                            "pname": parent.fullname, "myallgroup": myallgroup}
        if child.usertype == "user":
            noselectgroup = []
            selectgroup = []
            allselectgroup = child.group.exclude(state="9")
            for group in allgroup:
                if group in allselectgroup:
                    selectgroup.append(
                        {"groupname": group.name, "id": group.id})
                else:
                    noselectgroup.append(
                        {"groupname": group.name, "id": group.id})
            node["data"] = {"pname": parent.fullname, "username": child.user.username, "fullname": child.fullname,
                            "phone": child.phone, "email": child.user.email, "noselectgroup": noselectgroup,
                            "selectgroup": selectgroup}
        node["children"] = get_org_tree(child, selectid, allgroup)
        try:
            if int(selectid) == child.id:
                node["state"] = {"selected": True}
        except:
            pass
        nodes.append(node)
    return nodes


def organization(request, funid):
    if request.user.is_authenticated():
        try:
            errors = []
            title = "请选择组织"
            selectid = ""
            id = ""
            pid = ""
            pname = ""
            noselectgroup = []
            selectgroup = []
            username = ""
            fullname = ""
            orgname = ""
            phone = ""
            email = ""
            password = ""
            mytype = ""
            remark = ""
            hiddendiv = "hidden"
            hiddenuser = "hidden"
            hiddenorg = "hidden"
            newpassword = "hidden"
            editpassword = ""

            allgroup = Group.objects.exclude(state="9")
            if request.method == 'POST':
                hiddendiv = ""
                id = request.POST.get('id')
                pid = request.POST.get('pid')
                mytype = request.POST.get('mytype')
                try:
                    id = int(id)
                except:
                    raise Http404()
                try:
                    pid = int(pid)
                except:
                    raise Http404()

                if 'usersave' in request.POST:
                    hiddenuser = ""
                    hiddenorg = "hidden"
                    grouplist = request.POST.getlist('source')
                    noselectgroup = []
                    selectgroup = []
                    for group in allgroup:
                        if str(group.id) in grouplist:
                            selectgroup.append(
                                {"groupname": group.name, "id": group.id})
                        else:
                            noselectgroup.append(
                                {"groupname": group.name, "id": group.id})
                    pname = request.POST.get('pname')
                    username = request.POST.get('myusername', '')
                    fullname = request.POST.get('fullname', '')
                    phone = request.POST.get('phone', '')
                    email = request.POST.get('email', '')
                    password = request.POST.get('password', '')

                    newpassword = ""
                    editpassword = "hidden"

                    if id == 0:
                        selectid = pid
                        title = "新建"
                        alluser = User.objects.filter(
                            username=username)
                        if username.strip() == '':
                            errors.append('用户名不能为空。')
                        else:
                            if password.strip() == '':
                                errors.append('密码不能为空。')
                            else:
                                if fullname.strip() == '':
                                    errors.append('姓名不能为空。')
                                else:
                                    if (len(alluser) > 0):
                                        errors.append(
                                            '用户名:' + username + '已存在。')
                                    else:
                                        try:
                                            newuser = User()
                                            newuser.username = username
                                            newuser.set_password(
                                                password)
                                            newuser.email = email
                                            newuser.save()
                                            # 用户扩展信息 profile
                                            profile = UserInfo()  # e*************************
                                            profile.user_id = newuser.id
                                            profile.phone = phone
                                            profile.fullname = fullname

                                            try:
                                                porg = UserInfo.objects.get(
                                                    id=pid)
                                            except:
                                                raise Http404()
                                            profile.pnode = porg
                                            profile.usertype = "user"
                                            sort = 1
                                            try:
                                                maxorg = UserInfo.objects.filter(
                                                    pnode=porg).latest('sort')
                                                sort = maxorg.sort + 1
                                            except:
                                                pass
                                            profile.sort = sort
                                            profile.save()
                                            for group in grouplist:
                                                try:
                                                    group = int(
                                                        group)
                                                    mygroup = allgroup.get(
                                                        id=group)
                                                    profile.group.add(
                                                        mygroup)
                                                except ValueError:
                                                    raise Http404()
                                            title = fullname
                                            selectid = profile.id
                                            id = profile.id
                                            newpassword = "hidden"
                                            editpassword = ""
                                        except ValueError:
                                            raise Http404()
                    else:
                        selectid = id
                        title = fullname
                        exalluser = User.objects.filter(
                            username=username)
                        if username.strip() == '':
                            errors.append('用户名不能为空。')
                        else:
                            if fullname.strip() == '':
                                errors.append('姓名不能为空。')
                            else:
                                if (len(exalluser) > 0 and exalluser[0].userinfo.id != id):
                                    errors.append(
                                        '用户名:' + username + '已存在。')
                                else:
                                    try:
                                        alluserinfo = UserInfo.objects.get(
                                            id=id)
                                        alluser = alluserinfo.user
                                        alluser.email = email
                                        alluser.save()
                                        # 用户扩展信息 profile
                                        alluserinfo.phone = phone
                                        alluserinfo.fullname = fullname

                                        alluserinfo.save()
                                        alluserinfo.group.clear()
                                        for group in grouplist:
                                            try:
                                                group = int(group)
                                                mygroup = allgroup.get(
                                                    id=group)
                                                alluserinfo.group.add(
                                                    mygroup)
                                            except ValueError:
                                                raise Http404()
                                        title = fullname
                                    except:
                                        errors.append('保存失败。')
                else:
                    if 'orgsave' in request.POST:
                        hiddenuser = "hidden"
                        hiddenorg = ""
                        pname = request.POST.get('orgpname')
                        orgname = request.POST.get('orgname', '')
                        remark = request.POST.get('remark', '')

                        if id == 0:
                            selectid = pid
                            title = "新建"
                            try:
                                porg = UserInfo.objects.get(id=pid)
                            except:
                                raise Http404()
                            allorg = UserInfo.objects.filter(
                                fullname=orgname, pnode=porg)
                            if orgname.strip() == '':
                                errors.append('组织名称不能为空。')
                            else:
                                if (len(allorg) > 0):
                                    errors.append(orgname + '已存在。')
                                else:
                                    try:
                                        # 虚假用户，避免SQLServer中唯一索引null重复
                                        newuser = User()
                                        tmp_datetime = str(datetime.datetime.now())[-20:-1].encode('utf-8')
                                        newuser.username = base64.b64encode(tmp_datetime)  # 注意username的长度
                                        newuser.password = ''
                                        newuser.email = ''
                                        newuser.is_active = 0
                                        newuser.is_staff = 0
                                        newuser.save()

                                        profile = UserInfo()  # e*************************
                                        profile.user = newuser
                                        profile.fullname = orgname
                                        profile.pnode = porg
                                        profile.remark = remark
                                        profile.usertype = "org"
                                        sort = 1
                                        try:
                                            maxorg = UserInfo.objects.filter(
                                                pnode=porg).latest('sort')
                                            sort = maxorg.sort + 1
                                        except:
                                            pass
                                        profile.sort = sort
                                        profile.save()
                                        title = orgname
                                        selectid = profile.id
                                        id = profile.id
                                    except ValueError:
                                        raise Http404()
                        else:
                            selectid = id
                            title = orgname
                            try:
                                porg = UserInfo.objects.get(id=pid)
                            except:
                                raise Http404()
                            exalluser = UserInfo.objects.filter(
                                fullname=orgname, pnode=porg).exclude(state="9")
                            if orgname.strip() == '':
                                errors.append('组织名称不能为空。')
                            else:
                                if (len(exalluser) > 0 and exalluser[0].id != id):
                                    errors.append(username + '已存在。')
                                else:
                                    try:
                                        alluserinfo = UserInfo.objects.get(
                                            id=id)
                                        alluserinfo.fullname = orgname
                                        alluserinfo.remark = remark
                                        alluserinfo.save()
                                        title = orgname
                                    except:
                                        errors.append('保存失败。')
            treedata = []
            rootnodes = UserInfo.objects.order_by("sort").exclude(
                state="9").filter(pnode=None, usertype="org")
            if len(rootnodes) > 0:
                for rootnode in rootnodes:
                    root = {}
                    root["text"] = rootnode.fullname
                    root["id"] = rootnode.id
                    root["type"] = "org"
                    myallgroup = []
                    for group in allgroup:
                        myallgroup.append(
                            {"groupname": group.name, "id": group.id})
                    root["data"] = {"remark": rootnode.remark,
                                    "pname": "无", "myallgroup": myallgroup}
                    try:
                        if int(selectid) == rootnode.id:
                            root["state"] = {"opened": True, "selected": True}
                        else:
                            root["state"] = {"opened": True}
                    except:
                        root["state"] = {"opened": True}
                    root["children"] = get_org_tree(
                        rootnode, selectid, allgroup)
                    treedata.append(root)
            treedata = json.dumps(treedata)
            return render(request, 'organization.html',
                          {'username': request.user.userinfo.fullname, 'errors': errors, "id": id, "orgname": orgname,
                           "pid": pid, "pname": pname, "fullname": fullname, "phone": phone, "myusername": username,
                           "email": email, "password": password, "noselectgroup": noselectgroup,
                           "selectgroup": selectgroup, "remark": remark, "title": title, "mytype": mytype,
                           "hiddenuser": hiddenuser, "hiddenorg": hiddenorg, "newpassword": newpassword,
                           "editpassword": editpassword, "hiddendiv": hiddendiv, "treedata": treedata,
                           "pagefuns": getpagefuns(funid, request=request)})

        except Exception as e:
            print(e)
            return HttpResponseRedirect("/index")
    else:
        return HttpResponseRedirect("/login")


def orgdel(request):
    if request.user.is_authenticated():
        if 'id' in request.POST:
            id = request.POST.get('id', '')
            try:
                id = int(id)
            except:
                raise Http404()
            userinfo = UserInfo.objects.get(id=id)
            sort = userinfo.sort
            userinfo.state = "9"
            userinfo.sort = 9999
            userinfo.save()

            if userinfo.usertype == "user":
                user = userinfo.user
                user.is_active = 0
                user.save()

            userinfos = UserInfo.objects.filter(pnode=userinfo.pnode).filter(
                sort__gt=sort).exclude(state="9")
            if (len(userinfos) > 0):
                for myuserinfo in userinfos:
                    try:
                        myuserinfo.sort = myuserinfo.sort - 1
                        myuserinfo.save()
                    except:
                        pass

            return HttpResponse(1)
        else:
            return HttpResponse(0)


def orgmove(request):
    if request.user.is_authenticated():
        if 'id' in request.POST:
            id = request.POST.get('id', '')
            parent = request.POST.get('parent', '')
            old_parent = request.POST.get('old_parent', '')
            position = request.POST.get('position', '')
            old_position = request.POST.get('old_position', '')
            try:
                id = int(id)
            except:
                raise Http404()
            try:
                parent = int(parent)
            except:
                raise Http404()
            try:
                position = int(position)
            except:
                raise Http404()
            try:
                position = int(position)
            except:
                raise Http404()
            try:
                old_position = int(old_position)
            except:
                raise Http404()
            oldpuserinfo = UserInfo.objects.get(id=old_parent)
            oldsort = old_position + 1
            olduserinfos = UserInfo.objects.filter(
                pnode=oldpuserinfo).filter(sort__gt=oldsort)

            puserinfo = UserInfo.objects.get(id=parent)
            sort = position + 1
            userinfos = UserInfo.objects.filter(pnode=puserinfo).filter(sort__gte=sort).exclude(id=id).exclude(
                state="9")

            myuserinfo = UserInfo.objects.get(id=id)
            if puserinfo.usertype == "user":
                return HttpResponse("类型")
            else:
                usersame = UserInfo.objects.filter(pnode=puserinfo).filter(fullname=myuserinfo.fullname).exclude(
                    id=id).exclude(state="9")
                if (len(usersame) > 0):
                    return HttpResponse("重名")
                else:
                    if (len(olduserinfos) > 0):
                        for olduserinfo in olduserinfos:
                            try:
                                olduserinfo.sort = olduserinfo.sort - 1
                                olduserinfo.save()
                            except:
                                pass
                    if (len(userinfos) > 0):
                        for userinfo in userinfos:
                            try:
                                userinfo.sort = userinfo.sort + 1
                                userinfo.save()
                            except:
                                pass

                    try:
                        myuserinfo.pnode = puserinfo
                        myuserinfo.sort = sort
                        myuserinfo.save()
                    except:
                        pass
                    if parent != old_parent:
                        return HttpResponse(puserinfo.fullname + "^" + str(puserinfo.id))
                    else:
                        return HttpResponse("0")


def orgpassword(request):
    if request.user.is_authenticated():
        if 'id' in request.POST:
            id = request.POST.get('id')
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            try:
                offset = int(id)
                userinfo = UserInfo.objects.get(id=id)
                user = userinfo.user
                user.set_password(password1)
                user.save()
                return HttpResponse("1")
            except:
                HttpResponse('修改密码失败，请于管理员联系。')


def group(request, funid):
    if request.user.is_authenticated():
        try:
            allgroup = Group.objects.exclude(state="9")

            return render(request, 'group.html',
                          {'username': request.user.userinfo.fullname,
                           "allgroup": allgroup, "pagefuns": getpagefuns(funid, request)})
        except:
            return HttpResponseRedirect("/index")
    else:
        return HttpResponseRedirect("/login")


def groupsave(request):
    if 'id' in request.POST:
        result = {}
        id = request.POST.get('id', '')
        name = request.POST.get('name', '')
        remark = request.POST.get('remark', '')
        try:
            id = int(id)
        except:
            raise Http404()
        if name.strip() == '':
            result["res"] = '角色名称不能为空。'
        else:
            if id == 0:
                allgroup = Group.objects.filter(name=name).exclude(state="9")
                if (len(allgroup) > 0):
                    result["res"] = name + '已存在。'
                else:
                    groupsave = Group()
                    groupsave.name = name
                    groupsave.remark = remark
                    groupsave.save()
                    result["res"] = "新增成功。"
                    result["data"] = groupsave.id
            else:
                allgroup = Group.objects.filter(
                    name=name).exclude(id=id).exclude(state="9")
                if (len(allgroup) > 0):
                    result["res"] = name + '已存在。'
                else:
                    try:
                        groupsave = Group.objects.get(id=id)
                        groupsave.name = name
                        groupsave.remark = remark
                        groupsave.save()
                        result["res"] = "修改成功。"
                    except:
                        result["res"] = "修改失败。"
        return HttpResponse(json.dumps(result))


def groupdel(request):
    if 'id' in request.POST:
        result = ""
        id = request.POST.get('id', '')
        try:
            id = int(id)
        except:
            raise Http404()
        allgroup = Group.objects.filter(id=id)
        result = '角色不存在。'
        if (len(allgroup) > 0):
            groupsave = allgroup[0]
            groupsave.state = "9"
            groupsave.save()
            result = "删除成功。"
        else:
            result = '角色不存在。'
        return HttpResponse(result)


def getusertree(request):
    if 'id' in request.POST:
        id = request.POST.get('id', '')
        try:
            id = int(id)
        except:
            raise Http404()

        treedata = []
        groupsave = Group.objects.get(id=id)
        selectusers = groupsave.userinfo_set.exclude(state="9")

        rootnodes = UserInfo.objects.order_by("sort").exclude(
            state="9").filter(pnode=None, usertype="org")

        if len(rootnodes) > 0:
            for rootnode in rootnodes:
                root = {}
                root["text"] = rootnode.fullname
                root["id"] = "user_" + str(rootnode.id)
                root["type"] = "org"
                root["state"] = {"opened": True}
                root["children"] = group_get_user_tree(rootnode, selectusers)
                treedata.append(root)
        treedata = json.dumps(treedata)
        return HttpResponse(treedata)


def groupsaveusertree(request):
    if 'id' in request.POST:
        id = request.POST.get('id', '')
        selectedusers = request.POST.get('selecteduser', '')
        selectedusers = selectedusers.split(',')

        try:
            id = int(id)
        except:
            raise Http404()
        groupsave = Group.objects.get(id=id)
        groupsave.userinfo_set.clear()
        if len(selectedusers) > 0:
            for selecteduser in selectedusers:
                try:
                    myuser = UserInfo.objects.get(
                        id=int(selecteduser.replace("user_", "")))
                    if myuser.usertype == "user":
                        myuser.group.add(groupsave)
                except:
                    pass
        return HttpResponse("保存成功。")


def getfuntree(request):
    if 'id' in request.POST:
        id = request.POST.get('id', '')
        try:
            id = int(id)
        except:
            raise Http404()

        treedata = []
        groupsave = Group.objects.get(id=id)
        selectfuns = groupsave.fun.exclude(state="9")

        rootnodes = Fun.objects.order_by(
            "sort").filter(pnode=None, funtype="node")

        if len(rootnodes) > 0:
            for rootnode in rootnodes:
                root = {}
                root["text"] = rootnode.name
                root["id"] = "fun_" + str(rootnode.id)
                root["type"] = "node"
                root["state"] = {"opened": True}
                root["children"] = group_get_fun_tree(rootnode, selectfuns)
                treedata.append(root)
        treedata = json.dumps(treedata)
        return HttpResponse(treedata)


def groupsavefuntree(request):
    if 'id' in request.POST:
        id = request.POST.get('id', '')
        selectedfuns = request.POST.get('selectedfun', '')
        selectedfuns = selectedfuns.split(',')

        try:
            id = int(id)
        except:
            raise Http404()
        groupsave = Group.objects.get(id=id)
        groupsave.fun.clear()
        if len(selectedfuns) > 0:
            for selectedfun in selectedfuns:
                try:
                    myfun = Fun.objects.get(
                        id=int(selectedfun.replace("fun_", "")))
                    if myfun.funtype == "fun":
                        groupsave.fun.add(myfun)
                except:
                    pass
        return HttpResponse("保存成功。")


def get_format_date(pre_date, c_cycletype, type="C"):
    """格式化日期

    Args:
        pre_date (datetime): 格式化前日期
        cycletype (int): 周期类型
        type (string): 响应类型：C中文 E英文

    Returns:
        [datetime]: [格式化后日期]
    """
    format_date = ""
    try:
        if type == "C":
            if c_cycletype == "10":
                format_date = pre_date.strftime('%Y{y}%m{m}%d{d}').format(y='年', m='月', d='日')
            if c_cycletype == "11":
                format_date = pre_date.strftime('%Y{y}%m{m}').format(y='年', m='月')
            if c_cycletype == "12":
                format_date = pre_date.strftime('%Y{y} {q}').format(y='年', q='第{0}季度'.format(
                    (pre_date.month - 1) // 3 + 1))
            if c_cycletype == "13":
                if pre_date.month <= 6:
                    p = "上"
                else:
                    p = "下"
                format_date = pre_date.strftime('%Y{y} {p}').format(y='年', p='{0}半年'.format(p))
            if c_cycletype == "14":
                format_date = pre_date.strftime('%Y{y}').format(y='年')
        else:
            if c_cycletype in ["10", "12", "13"]:  # 日 季 半年
                format_date = "{:%Y-%m-%d}".format(pre_date)
            if c_cycletype == "11":  # 月
                format_date = "{:%Y-%m}".format(pre_date)
            if c_cycletype == "14":  # 年
                format_date = "{:%Y}".format(pre_date)
    except Exception as e:
        print(e)

    return format_date


def get_reporting_log(request):
    if request.user.is_authenticated():
        reporting_log = ReportingLog.objects.exclude(state='9').order_by('-id').select_related('adminapp', 'work')
        reporting_type_dict = {
            'del': '删除',
            'release': '发布',
            'save': '保存'
        }

        dict_list = DictList.objects.exclude(state='9').values()
        reporting_log_list = []

        for num, rl in enumerate(reporting_log):
            user = rl.user.userinfo.fullname if rl.user.userinfo else ''
            app = rl.adminapp.name if rl.adminapp else ''
            work = rl.work.name if rl.work else ''
            cycletype = int(rl.cycletype)
            for dl in dict_list:
                if cycletype == dl['id']:
                    cycletype = dl['name']
                    break
            reporting_type = ''
            try:
                reporting_type = reporting_type_dict[rl.type]
            except:
                pass
            time = ''
            try:
                time = '{:%Y-%m-%d %H:%M:%S}'.format(rl.write_time)
            except:
                pass

            # 报表时间 
            datadate = rl.datadate

            # 日报 月报 季报 半年报 年报
            #   2020年01月01日 日报
            #   2020年01月 月报
            #   2020年 第1季度 季报
            #   2020年 上半年/下半年 半年报
            #   2020年 年报

            datadate = get_format_date(datadate, rl.cycletype)
            user = '<span style="color:#3598DC">{0}</span>'.format(user)
            datadate = '<span style="color:#F7CA18">{0}</span>'.format(datadate)
            app = '<span style="color:#26C281">{0}</span>'.format(app)
            work = '<span style="color:#2ab4c0">{0}</span>'.format(work)
            operationtype = '<span style="color:#c5bf66">{0}</span>'.format(map_operation(rl.operationtype, True)) if rl.operationtype else ""
            log = '{user}{reporting_type}{app}{work}{datadate}{cycletype}报{operationtype}数据。'.format(**{
                'user': user,
                'app': app,
                'work': work if work else '',
                'reporting_type': reporting_type,
                'cycletype': cycletype,
                'operationtype': operationtype,
                'datadate': datadate
            })
            # 黄展翔 发布 动力中心经营统计计划部填报 2020-01-02日报数据
            reporting_log_list.append({
                'time': time,
                'log': log
            })
            if num > 50:
                break
        return JsonResponse({
            'data': reporting_log_list
        })
    else:
        return HttpResponseRedirect('/login')


def get_month_fdl(request):
    """
    一个月内 新厂、动力中心、老厂 所有机组：全场 分机组 的发电量曲线
    :param request:
    :return:
    """
    if request.user.is_authenticated():
        def get_target_30days_value_queryset(date, target):
            """
            处理隔年问题
            :param date:
            :param target:
            :return:
            """
            target_30days_values = []
            operation_type = target.operationtype
            date_year = date.year
            target_values = []
            if operation_type == "1":
                target_values = getmodels("Meterdata", str(date.year)).objects.exclude(state="9").filter(target__cycletype=10).filter(target=target).values("curvalue", "datadate")
            if operation_type == "15":
                target_values = getmodels("Entrydata", str(date.year)).objects.exclude(state="9").filter(target__cycletype=10).filter(target=target).values("curvalue", "datadate")
            if operation_type == "16":
                target_values = getmodels("Extractdata", str(date.year)).objects.exclude(state="9").filter(target__cycletype=10).filter(target=target).values("curvalue",
                                                                                                                                                              "datadate")
            if operation_type == "17":
                target_values = getmodels("Calculatedata", str(date.year)).objects.exclude(state="9").filter(target__cycletype=10).filter(target=target).values("curvalue",
                                                                                                                                                                "datadate")

            for i in range(1, 31):
                # 并非同一年，重新取数
                if date.year != date_year:
                    if operation_type == "1":
                        target_values = getmodels("Meterdata", str(date.year)).objects.exclude(state="9").filter(target__cycletype=10).filter(target=target).values(
                            "curvalue", "datadate"
                        )
                    if operation_type == "15":
                        target_values = getmodels("Entrydata", str(date.year)).objects.exclude(state="9").filter(target__cycletype=10).filter(target=target).values(
                            "curvalue", "datadate"
                        )
                    if operation_type == "16":
                        target_values = getmodels("Extractdata", str(date.year)).objects.exclude(state="9").filter(target__cycletype=10).filter(target=target).values(
                            "curvalue", "datadate"
                        )
                    if operation_type == "17":
                        target_values = getmodels("Calculatedata", str(date.year)).objects.exclude(state="9").filter(target__cycletype=10).filter(target=target).values(
                            "curvalue", "datadate"
                        )
                target_value = 0
                for tv in target_values:
                    if "{0:%Y-%m-%d}".format(tv["datadate"]) == "{0:%Y-%m-%d}".format(date):
                        target_value = float(tv["curvalue"]) if tv["curvalue"] else 0
                        break
                target_30days_values.append(target_value)
                date -= datetime.timedelta(days=1)

            return target_30days_values

        def get_categories(date):
            categories = []
            for i in range(1, 31):
                categories.append("{0:%Y-%m-%d}".format(date))
                date -= datetime.timedelta(days=1)

            return categories

        # 老厂经营统计
        #   FD_11_01(电表走字) FD_12_01(电表走字) FDL_9F(计算)
        # 动力中心经营统计
        #   DLZX_JYTJ_01_FDL(计算)  DLZX_JYTJ_02_FDL(计算) DLZX_JYTJ_FDL(计算)
        # 新厂经营统计
        #   NEW_JYTJ_01_FDL NEW_JYTJ_02_FDL NEW_JYTJ_FDL
        today = datetime.datetime.now()
        # today = datetime.datetime.strptime("2020-01-31", "%Y-%m-%d")

        dlzx_fdl_code_list = ["DLZX_JYTJ_01_FDL", "DLZX_JYTJ_02_FDL", "DLZX_JYTJ_FDL"]
        lc_fdl_code_list = ["FD_11_01", "FD_12_01", "FDL_9F"]
        xc_fdl_code_list = ["NEW_JYTJ_01_FDL", "NEW_JYTJ_02_FDL", "NEW_JYTJ_FDL"]
        colors = ["#3598dc", "#e7505a", "#32c5d2", "#67809F", "#f3c200"]

        dlzx = []
        lc = []
        xc = []

        for num, fdl_code in enumerate(dlzx_fdl_code_list):
            targets = Target.objects.exclude(state="9").filter(code=fdl_code)
            if targets.exists:
                target = targets[0]
                target_30days_values = get_target_30days_value_queryset(today, target)
                color = "#3598dc"
                try:
                    color = colors[num]
                except Exception:
                    pass

                dlzx.append({
                    "name": target.name,
                    "color": color,
                    "fdl": target_30days_values
                })
        for num, fdl_code in enumerate(lc_fdl_code_list):
            targets = Target.objects.exclude(state="9").filter(code=fdl_code)
            if targets.exists:
                target = targets[0]
                target_30days_values = get_target_30days_value_queryset(today, target)
                color = "#3598dc"
                try:
                    color = colors[num]
                except Exception:
                    pass

                lc.append({
                    "name": target.name,
                    "color": color,
                    "fdl": target_30days_values
                })
        for num, fdl_code in enumerate(xc_fdl_code_list):
            targets = Target.objects.exclude(state="9").filter(code=fdl_code)
            if targets.exists:
                target = targets[0]
                target_30days_values = get_target_30days_value_queryset(today, target)
                color = "#3598dc"
                try:
                    color = colors[num]
                except Exception:
                    pass

                xc.append({
                    "name": target.name,
                    "color": color,
                    "fdl": target_30days_values
                })

        categories = get_categories(today)
        return JsonResponse({
            "DLZX_JYTJ": {
                "fld_list": dlzx,
                "categories": categories
            },
            "LC_JYTJ": {
                "fld_list": lc,
                "categories": categories
            },
            "XC_JYTJ": {
                "fld_list": xc,
                "categories": categories
            }
        })
    else:
        return HttpResponseRedirect("/login")


def get_target_data_recently(code):
    """
    获取指标 最近有数据的一天的数据
    :param code:
    :return appointed_time_object:
    """
    data = {
        "target_name": "",
        "unit": "",
        "curvalue": 0,
        "cumulativemonth": 0,
        "cumulativeyear": 0
    }

    model_map = {
        "1": "Meterdata",
        "15": "Entrydata",
        "16": "Extractdata",
        "17": "Calculatedata",
    }
    targets = Target.objects.exclude(state="9").filter(code=code)
    if targets.exists():
        target = targets[0]
        operation_type = target.operationtype
        digit = target.digit

        data["unit"] = target.unity
        data["target_name"] = target.name

        model_name = ""
        try:
            model_name = model_map[operation_type]
        except Exception:
            pass
        # 操作类型: 计算、提取、录入、电表走字
        now_time = datetime.datetime.now()
        for i in range(1, 3):  # 2年内
            recent_object = getmodels(model_name, str(now_time.year)).objects.exclude(state="9").filter(
                target=target
            ).last()
            if recent_object:
                curvalue = 0
                cumulativemonth = 0
                cumulativeyear = 0

                try:
                    curvalue = float(round(recent_object.curvalue, digit))
                except Exception:
                    pass
                try:
                    cumulativemonth = float(round(recent_object.cumulativemonth, digit))
                except Exception:
                    pass
                try:
                    cumulativeyear = float(round(recent_object.cumulativeyear, digit))
                except Exception:
                    pass

                data["curvalue"] = curvalue
                data["cumulativemonth"] = cumulativemonth
                data["cumulativeyear"] = cumulativeyear
                break
            now_time = now_time - datetime.timedelta(days=1)
        else:
            data["curvalue"] = 0
            data["cumulativemonth"] = 0
            data["cumulativeyear"] = 0

    return data


def get_appointed_time_data(code, appointed_time):
    """
    获取指标指定时间的数据对象
    :param code:
    :param appointed_time:
    :return appointed_time_object:
    """
    data = {
        "target_name": "",
        "curvalue": 0,
        "cumulativemonth": 0,
        "cumulativeyear": 0
    }

    model_map = {
        "1": "Meterdata",
        "15": "Entrydata",
        "16": "Extractdata",
        "17": "Calculatedata",
    }
    targets = Target.objects.exclude(state="9").filter(code=code)
    if targets.exists():
        target = targets[0]
        operation_type = target.operationtype
        digit = target.digit
        appointed_time_object = []

        model_name = ""
        try:
            model_name = model_map[operation_type]
        except Exception:
            pass
        # 操作类型: 计算、提取、录入、电表走字
        appointed_time_object = getmodels(model_name, str(appointed_time.year)).objects.exclude(state="9").filter(
            datadate=appointed_time.date()
        ).filter(target=target)

        if appointed_time_object:
            appointed_time_object = appointed_time_object[0]

            curvalue = 0
            cumulativemonth = 0
            cumulativeyear = 0

            try:
                curvalue = float(round(appointed_time_object.curvalue, digit))
            except Exception:
                pass
            try:
                cumulativemonth = float(round(appointed_time_object.cumulativemonth, digit))
            except Exception:
                pass
            try:
                cumulativeyear = float(round(appointed_time_object.cumulativeyear, digit))
            except Exception:
                pass
            data = {
                "target_name": target.name,
                "curvalue": curvalue,
                "cumulativemonth": cumulativemonth,
                "cumulativeyear": cumulativeyear
            }
        else:
            data = {
                "target_name": target.name,
                "curvalue": 0,
                "cumulativemonth": 0,
                "cumulativeyear": 0
            }

    return data


def get_important_targets(request):
    """
    获取燃热、煤机、9F重要指标 最近有数据的一天
        煤机：发电量、上网电量、供热量、耗煤量、负荷率、厂用电率、发电标煤耗、供电标煤耗、供热标煤耗
        燃热：发电量、上网电量、供热量、负荷率、厂用电率、发电标煤耗、供电标煤耗、供热标煤耗 -> 没有耗煤量
        9F：发电量、上网电量、耗气量、负荷率、厂用电率、发电标煤耗、供电标煤耗
    发电量月计划、上网电量月计划
    
    :param request:
    :return:
    """
    if request.user.is_authenticated():
        status = 1
        data = {
            "RR": {
                "JYZB": [
                    {"target": "DLZX_JYTJ_FDL", "v_type": "cumulativeyear", "value": 0},
                    {"target": "DLZX_JYTJ_SWDL", "v_type": "cumulativeyear", "value": 0},
                    {"target": "DLZX_JYTJ_ZGRL_NEW", "v_type": "cumulativeyear", "value": 0},
                    {"target": "DLZX_JYTJ_FHL_Y", "v_type": "curvalue", "value": 0},
                    {"target": "DLZX_JYTJ_ZHCYDL_Y", "v_type": "curvalue", "value": 0},
                    {"target": "DLZX_JYTJ_FDBZMH_Y", "v_type": "curvalue", "value": 0},
                    {"target": "DLZX_JYTJ_GDBZMH_Y", "v_type": "curvalue", "value": 0},
                    {"target": "DLZX_JYTJ_GRBZMH_Y", "v_type": "curvalue", "value": 0}
                ],
                "HBZB": [
                    {"target": "DLZX_HB_01_RJPFND_SO2", "v_type": "curvalue", "value": 0},
                    {"target": "DLZX_HB_02_RJPFND_SO2", "v_type": "curvalue", "value": 0},
                    {"target": "DLZX_HB_01_RJ_SO2", "v_type": "curvalue", "value": 0},
                    {"target": "DLZX_HB_02_RJ_SO2", "v_type": "curvalue", "value": 0},
                    {"target": "DLZX_HB_01_RJ_YQPFL", "v_type": "curvalue", "value": 0},
                    {"target": "DLZX_HB_02_RJ_YQPFL", "v_type": "curvalue", "value": 0},
                    {"target": "DLZX_HB_01_RJPFND_NOx", "v_type": "curvalue", "value": 0},
                    {"target": "DLZX_HB_02_RJPFND_NOx", "v_type": "curvalue", "value": 0},
                    {"target": "DLZX_HB_01_RJ_NOx", "v_type": "curvalue", "value": 0},
                    {"target": "DLZX_HB_02_RJ_NOx", "v_type": "curvalue", "value": 0}
                ],
                "FDL_JH": [
                    [  # 发电量年计划
                        {"target": "DLZX_JYTJ_FDL_NJH", "v_type": "curvalue", "value": 0},  # 计划
                        {"target": "DLZX_JYTJ_FDL", "v_type": "cumulativeyear", "value": 0}  # 已完成
                    ],
                    [  # 上网电量年计划
                        {"target": "DLZX_JYTJ_SWDL_NJH", "v_type": "curvalue", "value": 0},  # 计划
                        {"target": "DLZX_JYTJ_SWDL", "v_type": "cumulativeyear", "value": 0}  # 已完成
                    ],
                ]
            },
            "MJ": {
                "JYZB": [
                    {"target": "NEW_JYTJ_FDL", "v_type": "cumulativeyear", "value": 0},
                    {"target": "NEW_JYTJ_SWDL", "v_type": "cumulativeyear", "value": 0},
                    {"target": "NEW_JYTJ_GRL", "v_type": "cumulativeyear", "value": 0},
                    {"target": "NEW_JYTJ_HML", "v_type": "cumulativeyear", "value": 0},
                    {"target": "NEW_JYTJ_FHL_Y", "v_type": "curvalue", "value": 0},
                    {"target": "NEW_JYTJ_ZHCYDL_Y", "v_type": "curvalue", "value": 0},
                    {"target": "NEW_JYTJ_FDBZMH_Y", "v_type": "curvalue", "value": 0},
                    {"target": "NEW_JYTJ_GDBZMH_Y", "v_type": "curvalue", "value": 0},
                    {"target": "NEW_JYTJ_GRBZMH_Y", "v_type": "curvalue", "value": 0}
                ],
                "HBZB": [
                    {"target": "NEW_HB_01_SO2ND", "v_type": "curvalue", "value": 0},
                    {"target": "NEW_HB_02_SO2ND", "v_type": "curvalue", "value": 0},
                    {"target": "NEW_HB_01_SO2PFL", "v_type": "curvalue", "value": 0},
                    {"target": "NEW_HB_02_SO2PFL", "v_type": "curvalue", "value": 0},
                    {"target": "NEW_HB_01_YQPFL", "v_type": "curvalue", "value": 0},
                    {"target": "NEW_HB_02_YQPFL", "v_type": "curvalue", "value": 0},
                    {"target": "NEW_HB_01_NOXND", "v_type": "curvalue", "value": 0},
                    {"target": "NEW_HB_02_NOXND", "v_type": "curvalue", "value": 0},
                    {"target": "NEW_HB_01_NOXPFL", "v_type": "curvalue", "value": 0},
                    {"target": "NEW_HB_02_NOXPFL", "v_type": "curvalue", "value": 0}
                ],
                "FDL_JH": [
                    [  # 发电量年计划
                        {"target": "NEW_JYTJ_FDLNJH", "v_type": "curvalue", "value": 0},  # 计划
                        {"target": "NEW_JYTJ_FDL", "v_type": "cumulativeyear", "value": 0}  # 已完成
                    ],
                    [  # 上网电量年计划
                        {"target": "NEW_JYTJ_SWDLNJH", "v_type": "curvalue", "value": 0},  # 计划
                        {"target": "NEW_JYTJ_SWDL", "v_type": "cumulativeyear", "value": 0}  # 已完成
                    ],
                ]
            },
            "9F": {
                "JYZB": [
                    {"target": "FDL_9F", "v_type": "cumulativeyear", "value": 0},
                    {"target": "SWDL_9F", "v_type": "cumulativeyear", "value": 0},
                    {"target": "FDHQ", "v_type": "cumulativeyear", "value": 0},
                    {"target": "FHL_9F", "v_type": "cumulativeyear", "value": 0},
                    {"target": "ZHCYDL_9F_Y", "v_type": "curvalue", "value": 0},
                    {"target": "FDBZMHLV_9F_NLJ", "v_type": "curvalue", "value": 0},
                    {"target": "ZHGDBZMHL_9F_Y", "v_type": "curvalue", "value": 0,
                     }],
                "HBZB": [
                    {"target": "OLD_HB_11_NOXPJSCND", "v_type": "curvalue", "value": 0},
                    {"target": "OLD_HB_12_NOXPJSCND", "v_type": "curvalue", "value": 0},
                    {"target": "OLD_HB_11_NOXPJZSND", "v_type": "curvalue", "value": 0},
                    {"target": "OLD_HB_12_NOXPJZSND", "v_type": "curvalue", "value": 0},
                    {"target": "OLD_HB_11_NOXPFL", "v_type": "curvalue", "value": 0},
                    {"target": "OLD_HB_12_NOXPFL", "v_type": "curvalue", "value": 0},
                    {"target": "OLD_HB_11_YQPFL", "v_type": "curvalue", "value": 0},
                    {"target": "OLD_HB_12_YQPFL", "v_type": "curvalue", "value": 0},
                ],
                "FDL_JH": [
                    [  # 发电量年计划
                        {"target": "9F_FDL_NJH", "v_type": "curvalue", "value": 0},  # 计划
                        {"target": "FDL_9F", "v_type": "cumulativeyear", "value": 0}  # 已完成
                    ],
                    [  # 上网电量年计划
                        {"target": "9F_SWDL_NJH", "v_type": "curvalue", "value": 0},  # 计划
                        {"target": "SWDL_9F", "v_type": "cumulativeyear", "value": 0}  # 已完成
                    ],
                ]
            },
        }

        # now = datetime.datetime.now()
        # now = datetime.datetime.strptime("2020-07-21", "%Y-%m-%d")

        # **************
        #   燃热
        # **************
        #   经营指标
        rr_jyzbs = data["RR"]["JYZB"]

        for rr_jyzb in rr_jyzbs:
            rr_jyzb_code = rr_jyzb["target"]
            recent_data = get_target_data_recently(rr_jyzb_code)
            rr_jyzb["value"] = recent_data.get(rr_jyzb["v_type"], 0)
            rr_jyzb["target_name"] = recent_data["target_name"]
            rr_jyzb["unit"] = recent_data["unit"]

        #   环保指标
        rr_hbzbs = data["RR"]["HBZB"]

        for rr_hbzb in rr_hbzbs:
            rr_hbzb_code = rr_hbzb["target"]
            recent_data = get_target_data_recently(rr_hbzb_code)
            rr_hbzb["value"] = recent_data.get(rr_hbzb["v_type"], 0)
            rr_hbzb["target_name"] = recent_data["target_name"]
            rr_hbzb["unit"] = recent_data["unit"]
        #   年计划
        rr_njhs = data["RR"]["FDL_JH"]

        for rr_njh in rr_njhs:
            for rn in rr_njh:
                recent_data = get_target_data_recently(rn["target"])
                rn["value"] = recent_data.get(rn["v_type"], 0)
                rn["target_name"] = recent_data["target_name"]
        # **************
        #   煤机
        # **************
        #   经营指标
        mj_jyzbs = data["MJ"]["JYZB"]

        for mj_jyzb in mj_jyzbs:
            mj_jyzb_code = mj_jyzb["target"]
            recent_data = get_target_data_recently(mj_jyzb_code)
            mj_jyzb["value"] = recent_data.get(mj_jyzb["v_type"], 0)
            mj_jyzb["target_name"] = recent_data["target_name"]
            mj_jyzb["unit"] = recent_data["unit"]

        #   环保指标
        mj_hbzbs = data["MJ"]["HBZB"]

        for mj_hbzb in mj_hbzbs:
            mj_hbzb_code = mj_hbzb["target"]
            recent_data = get_target_data_recently(mj_hbzb_code)
            mj_hbzb["value"] = recent_data.get(mj_hbzb["v_type"], 0)
            mj_hbzb["target_name"] = recent_data["target_name"]
            mj_hbzb["unit"] = recent_data["unit"]

        #   年计划
        mj_njhs = data["MJ"]["FDL_JH"]

        for mj_njh in mj_njhs:
            for mn in mj_njh:
                recent_data = get_target_data_recently(mn["target"])
                mn["value"] = recent_data.get(mn["v_type"], 0)
                mn["target_name"] = recent_data["target_name"]
        # **************
        #   9F
        # **************
        #   经营指标
        jf_jyzbs = data["9F"]["JYZB"]

        for jf_jyzb in jf_jyzbs:
            jf_jyzb_code = jf_jyzb["target"]
            recent_data = get_target_data_recently(jf_jyzb_code)
            jf_jyzb["value"] = recent_data.get(jf_jyzb["v_type"], 0)
            jf_jyzb["target_name"] = recent_data["target_name"]
            jf_jyzb["unit"] = recent_data["unit"]

        #   环保指标
        jf_hbzbs = data["9F"]["HBZB"]

        for jf_hbzb in jf_hbzbs:
            jf_hbzb_code = jf_hbzb["target"]
            recent_data = get_target_data_recently(jf_hbzb_code)
            jf_hbzb["value"] = recent_data.get(jf_hbzb["v_type"], 0)
            jf_hbzb["target_name"] = recent_data["target_name"]
            jf_hbzb["unit"] = recent_data["unit"]

        #   年计划
        jf_njhs = data["9F"]["FDL_JH"]

        for jf_njh in jf_njhs:
            for jn in jf_njh:
                recent_data = get_target_data_recently(jn["target"])
                jn["value"] = recent_data.get(jn["v_type"], 0)
                jn["target_name"] = recent_data["target_name"]

        return JsonResponse({
            "status": status,
            "data": data
        })
    else:
        return HttpResponseRedirect("/login")


def report_search(request, funid):
    if request.user.is_authenticated():
        return render(request, 'report_search.html', {
            'username': request.user.userinfo.fullname, "pagefuns": getpagefuns(funid, request)
        })
    else:
        return HttpResponseRedirect('/login')


def get_report_search_data(request):
    """获取已发布报表时间等信息，以树的形式展示
    镇海电厂
        > 应用
            > 周期
                > 报表名称
                    时间 状态 
    """
    if request.user.is_authenticated():
        status = 1
        info = ""

        # 应用 App
        # 报表类型 DictList DictIndex=7
        # 报表记录 ReportSubmit ReportModel
        apps = App.objects.exclude(state="9")
        cycles = DictList.objects.exclude(state="9").filter(dictindex_id=12).values()
        report_submits = ReportSubmit.objects.filter(state="1").order_by("-id").values(
            "id", "app_id", "report_model_id", "report_model__name", "state", "person", "write_time", "report_time",
            "report_model__report_type", "report_model__code"
        )
        report_models = ReportModel.objects.exclude(state="9").values()

        # 周期 报表类型对应字典
        #   根据周期匹配报表类型
        compile_dict = {
            10: 22,
            11: 23,
            12: 24,
            13: 25,
            14: 26
        }

        root_info = {}
        root_info["text"] = "镇海电厂"
        root_info["type"] = "node"
        root_info["state"] = {'opened': True}

        app_list = []
        for app in apps:
            app_info = {}
            app_info["text"] = app.name
            app_info["type"] = "node"
            app_info["data"] = {
                "name": app.name,
                "code": app.code
            }
            funs = app.fun_set.exclude(state="9").filter(url__contains="report_submit")
            fun_id = funs[0].id if funs else ""
            cur_url = funs[0].url if funs else ""

            cycle_list = []
            for cycle in cycles:
                cycle_info = {}
                cycle_info["text"] = cycle['name']
                cycle_info["type"] = "node"
                cycle_info["data"] = {
                    "id": cycle["id"],
                    "name": cycle["name"]
                }

                report_model_list = []
                for report_model in report_models:
                    report_model_info = {}

                    report_type = ""
                    try:
                        report_type = compile_dict[cycle["id"]]
                    except Exception:
                        pass
                    if report_model["app_id"] == app.id and report_model["report_type"] == str(report_type):
                        report_model_info["text"] = report_model["name"]
                        report_model_info["type"] = "file"

                        # 报表数据
                        report_submit_list = []

                        for report_submit in report_submits:
                            if report_submit["report_model_id"] == report_model["id"]:
                                # 周期类型 + 时间
                                params = "?report_type={report_type}&report_time={report_time}".format(**{
                                    "report_type": report_type,
                                    "report_time": get_format_date(report_submit["report_time"], str(cycle["id"]), type="E") if report_submit["report_time"] else "",
                                })

                                if fun_id:
                                    url = "{0}/{1}{2}".format(cur_url, fun_id, params) if not cur_url.endswith("/") else "{0}{1}{2}".format(cur_url, fun_id, params)
                                else:
                                    url = "/index"

                                report_submit_list.append({
                                    "name": report_submit["report_model__name"],
                                    "write_time": "{0:%Y-%m-%d %H:%M:%S}".format(report_submit["write_time"]) if report_submit["write_time"] else "",
                                    "report_time": get_format_date(report_submit["report_time"], str(cycle["id"])) if report_submit["report_time"] else "",
                                    "person": report_submit["person"],
                                    "code": report_submit["report_model__code"],

                                    "url": url,
                                })
                        report_model_info["data"] = report_submit_list
                        report_model_list.append(report_model_info)

                if not report_model_list:
                    continue
                cycle_info["children"] = report_model_list
                cycle_list.append(cycle_info)

            app_info["children"] = cycle_list
            app_list.append(app_info)
        root_info["children"] = app_list

        return JsonResponse({
            "status": status,
            "info": info,
            "data": root_info
        })
    else:
        return HttpResponseRedirect('/login')


def target_value_search(request, funid):
    if request.user.is_authenticated():
        # 管理应用id
        app_id = ""
        try:
            funid = int(funid)
        except ValueError:
            pass
        c_app = get_app_from_fun(funid)
        if not c_app["err"]:
            app_id = c_app["app_id"]

        # 月初 -> 现在
        n_time = datetime.datetime.now()
        end_date = "{:%Y-%m-%d}".format(n_time)
        start_date = "{:%Y-%m-%d}".format(n_time.replace(day=1))
        return render(request, 'target_value_search.html', {
            'username': request.user.userinfo.fullname, "pagefuns": getpagefuns(funid, request),
            "app_id": app_id, "start_date": start_date, "end_date": end_date,
        })
    else:
        return HttpResponseRedirect('/login')


def get_target_value(c_target, start_date, end_date):
    """
    start_date与end_date必须在同一年
    :param operation_type:
    :param start_date:
    :param end_date:
    :return:
    """
    data = []
    model_map = {
        "1": "Meterdata",
        "15": "Entrydata",
        "16": "Extractdata",
        "17": "Calculatedata",
    }
    if c_target:
        operation_type = c_target.operationtype
        target_id = c_target.id
        model_name = ""
        try:
            model_name = model_map[operation_type]
        except Exception:
            pass

        appointed_time_object = None

        if model_name:
            if not start_date and end_date:
                appointed_time_object = getmodels(model_name, str(end_date.year)).objects.exclude(state="9").filter(target_id=target_id).filter(datadate__lte=end_date.date())
            if start_date and not end_date:
                appointed_time_object = getmodels(model_name, str(start_date.year)).objects.exclude(state="9").filter(target_id=target_id).filter(datadate__gte=start_date.date())
            if all([start_date, end_date]):
                appointed_time_object = getmodels(model_name, str(start_date.year)).objects.exclude(state="9").filter(target_id=target_id).filter(
                    Q(datadate__gte=start_date.date()) & Q(datadate__lte=end_date.date())
                )
        # 对值的处理
        for ato in appointed_time_object.values(
                "curvalue", "target__name", "target__code", "datadate", "target__digit",
                "cumulativemonth", "cumulativequarter", "cumulativehalfyear", "cumulativeyear",
        ):
            data.append({
                "name": ato["target__name"],
                "code": ato["target__code"],
                "curvalue": round(ato["curvalue"] if ato["curvalue"] else 0, ato["target__digit"]),
                "cumulativemonth": round(ato["cumulativemonth"] if ato["cumulativemonth"] else 0, ato["target__digit"]),
                "cumulativequarter": round(ato["cumulativequarter"] if ato["cumulativequarter"] else 0, ato["target__digit"]),
                "cumulativehalfyear": round(ato["cumulativehalfyear"] if ato["cumulativehalfyear"] else 0, ato["target__digit"]),
                "cumulativeyear": round(ato["cumulativeyear"] if ato["cumulativeyear"] else 0, ato["target__digit"]),
                "datadate": ato["datadate"]
            })

    return data


def get_target_search_data(request):
    """
    查询指标数据
        start_date end_date 可能不在同一年
    :param request:
    :return:
    """
    if request.user.is_authenticated():
        status = 1
        info = ""
        all_data = []

        target = request.POST.get("target", "")
        start_date = request.POST.get("start_date", "")
        end_date = request.POST.get("end_date", "")
        app_id = request.POST.get("app_id", "")
        try:
            app_id = int(app_id)
        except ValueError:
            pass
        if not target:
            status = 0
            info = '指标代码或者指标名称未填写。'
        elif not start_date:
            status = 0
            info = "开始时间未选择。"
        elif not end_date:
            status = 0
            info = "结束时间未选择。"
        else:
            # 判断开始时间与结束时间是否在同一年
            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")

            if start_date > end_date:
                status = 0
                info = "开始时间不得迟于结束时间。"
            else:
                c_targets = Target.objects.exclude(state="9").filter(Q(name__icontains=target) | Q(code__icontains=target)).filter(
                    Q(adminapp__id=app_id) | Q(app__id=app_id)
                )
                for c_target in c_targets:
                    data = []

                    start_date_year = start_date.year
                    end_date_year = end_date.year
                    delta_year = end_date_year - start_date_year
                    if delta_year == 0:  # 同一年
                        target_values = get_target_value(c_target, start_date, end_date)
                        data = [{
                            "name": tv["name"],
                            "code": tv["code"],
                            "curvalue": tv["curvalue"],
                            "cumulativemonth": tv["cumulativemonth"],
                            "cumulativequarter": tv["cumulativequarter"],
                            "cumulativehalfyear": tv["cumulativehalfyear"],
                            "cumulativeyear": tv["cumulativeyear"],
                            "time": "{0:%Y-%m-%d}".format(tv["datadate"]) if tv["datadate"] else "",
                        } for tv in target_values]
                    else:
                        # 开始时间到年底
                        s_target_values = [{
                            "name": tv["name"],
                            "code": tv["code"],
                            "curvalue": tv["curvalue"],
                            "cumulativemonth": tv["cumulativemonth"],
                            "cumulativequarter": tv["cumulativequarter"],
                            "cumulativehalfyear": tv["cumulativehalfyear"],
                            "cumulativeyear": tv["cumulativeyear"],
                            "time": "{0:%Y-%m-%d}".format(tv["datadate"]) if tv["datadate"] else "",
                        } for tv in get_target_value(c_target, start_date, None)]
                        # 结束时间到年初
                        e_target_values = [{
                            "name": tv["name"],
                            "code": tv["code"],
                            "curvalue": tv["curvalue"],
                            "cumulativemonth": tv["cumulativemonth"],
                            "cumulativequarter": tv["cumulativequarter"],
                            "cumulativehalfyear": tv["cumulativehalfyear"],
                            "cumulativeyear": tv["cumulativeyear"],
                            "time": "{0:%Y-%m-%d}".format(tv["datadate"]) if tv["datadate"] else "",
                        } for tv in get_target_value(c_target, None, end_date)]

                        m_target_values = []
                        # 2017 2019 2  >>> 2018
                        if delta_year > 1:
                            for i in range(0, delta_year):
                                start_date_year += 1
                                start_date = datetime.datetime(start_date_year, 1, 1)
                                target_values = get_target_value(c_target, start_date, None)
                                m_data = [{
                                    "name": tv["name"],
                                    "code": tv["code"],
                                    "curvalue": tv["curvalue"],
                                    "cumulativemonth": tv["cumulativemonth"],
                                    "cumulativequarter": tv["cumulativequarter"],
                                    "cumulativehalfyear": tv["cumulativehalfyear"],
                                    "cumulativeyear": tv["cumulativeyear"],
                                    "time": "{0:%Y-%m-%d}".format(tv["datadate"]) if tv["datadate"] else "",
                                } for tv in target_values]
                                if m_data:
                                    m_target_values.extend(m_data)

                        data = s_target_values + m_target_values + e_target_values

                    all_data.extend(data)
        return JsonResponse({
            "status": status,
            "info": info,
            "data": sorted(all_data, key=lambda e: e.__getitem__('time'), reverse=True) if all_data else []
        })
    else:
        return HttpResponseRedirect('/login')


def target_statistic(request, funid):
    if request.user.is_authenticated():
        # 管理应用id
        app_id = ""
        try:
            funid = int(funid)
        except ValueError:
            pass
        c_app = get_app_from_fun(funid)
        if not c_app["err"]:
            app_id = c_app["app_id"]

        # 周期类型
        cycle_list = DictList.objects.exclude(state="9").filter(dictindex_id=12)

        targets = Target.objects.exclude(state="9").filter(
            Q(adminapp__id=app_id) | Q(app__id=app_id)
        ).values("id", "name", "cycletype")

        return render(request, 'target_statistic.html', {
            'username': request.user.userinfo.fullname, "pagefuns": getpagefuns(funid, request),
            "cycle_list": cycle_list, "targets": list(targets),  # 解决 remaining elements truncated
            "app_id": app_id,
        })
    else:
        return HttpResponseRedirect('/login')


def target_statistic_data(request):
    """
    data = [{
        "id": 1,
        "name": "查询1",
        "type": "10",
        "type_name": "日",
        "remark": "说明1",
        "target_col": [{
            "name": "第一列",
            "targets": [{"target_id": 35, "new_target_name": "新指标名1", "target_name": "指标1"}, {"target_id": 36, "new_target_name": "新指标名2", "target_name": "指标2"}],
            "remark": "指标列说明",
            "statistc_type": "0"
        }, {
            "name": "第二列",
            "targets": [{"target_id": 37, "new_target_name": "新指标名3"}],
            "remark": "指标列说明",
            "statistc_type": "1"
        }]
    }, {
        "id": 2,
        "name": "查询2",
        "type": "11",
        "type_name": "月",
        "remark": "说明2",
        "target_col": [],
    }]
    :param request:
    :return:
    """
    if request.user.is_authenticated():
        status = 1
        info = ""
        data = []

        target_statistics = TargetStatistic.objects.exclude(state="9")
        type_list = DictList.objects.filter(dictindex_id=12).values()

        for target_statistic in target_statistics:
            if request.user.userinfo == target_statistic.user or request.user.is_superuser:
                type_name = ""
                for tl in type_list:
                    if str(tl['id']) == target_statistic.type:
                        type_name = tl['name']

                target_col = eval(target_statistic.col_data)
                data.append({
                    "id": target_statistic.id,
                    "name": target_statistic.name,
                    "type": target_statistic.type,
                    "type_name": type_name,
                    "remark": target_statistic.remark,
                    "target_col": target_col
                })

        return JsonResponse({
            "status": status,
            "info": info,
            "data": data
        })
    else:
        return HttpResponseRedirect('/login')


def target_statistic_save(request):
    if request.user.is_authenticated():
        status = 1
        info = ""

        id = request.POST.get("id", "")
        col_data = request.POST.get("col_data", "")
        name = request.POST.get("name", "")
        type = request.POST.get("type", "")
        remark = request.POST.get("remark", "")

        try:
            id = int(id)
        except Exception:
            status = 0
            info = "网络异常。"
        else:
            if not name:
                status = 0
                info = "查询名不能为空。"
            elif not type:
                status = 0
                info = "查询类型不能为空。"
            else:
                try:
                    col_data = json.loads(col_data)
                except Exception:
                    pass
                if id == 0:
                    try:
                        TargetStatistic.objects.create(**{
                            "name": name,
                            "type": type,
                            "remark": remark,
                            "col_data": col_data,
                            "user": request.user.userinfo,
                        })
                        info = "新增成功。"
                    except Exception as e:
                        stauts = 0
                        info = "新增查询失败。"
                else:
                    try:
                        TargetStatistic.objects.filter(id=id).update(**{
                            "name": name,
                            "type": type,
                            "remark": remark,
                            "col_data": col_data,
                            "user": request.user.userinfo,
                        })
                        info = "修改成功。"
                    except Exception as e:
                        status = 0
                        info = "修改查询失败。"
        return JsonResponse({
            "status": status,
            "info": info
        })
    else:
        return HttpResponseRedirect("/login")


def target_statistic_del(request):
    if request.user.is_authenticated():
        status = 1
        info = "删除成功。"

        id = request.POST.get("id", "")

        try:
            TargetStatistic.objects.filter(id=int(id)).update(**{"state": "9"})
        except Exception:
            status = 0
            info = "删除失败。"

        return JsonResponse({
            "status": status,
            "info": info
        })
    else:
        return HttpResponseRedirect("/login")


def statistic_report(request):
    """

    @param request:
    @return: e_date
             s_date
             e_seasondate
             s_seasondate
             e_yeardate
             s_yeardate
    """
    if request.user.is_authenticated():
        date_type = request.GET.get("date_type", "")
        search_id = request.GET.get("search_id", "")

        # date_type: 日 月 季 半年 年 显示不同时间
        n_time = datetime.datetime.now()

        e_time = n_time.replace(hour=0, minute=0, second=0, microsecond=0)  # 结束时间
        e_date = e_time.strftime("%Y-%m-%d")
        s_time = n_time.replace(hour=0, minute=0, second=0, microsecond=0)  # 开始时间
        s_date = s_time.strftime("%Y-%m-%d")
        if date_type == '10':  # 日
            s_time = s_time - relativedelta(months=1)
            s_time = get_last_day_in_month(s_time)
            s_date = s_time.strftime("%Y-%m-%d")
        if date_type == '11':  # 月
            s_time = s_time - relativedelta(months=1)
            s_time = get_last_day_in_month(s_time)

            s_date = s_time.strftime("%Y-%m")
            e_date = e_time.strftime("%Y-%m")

        e_seasondate = ''
        s_seasondate = ''
        if date_type == '12':  # 季
            now = n_time
            month = (now.month - 1) - (now.month - 1) % 3 + 1
            now = (n_time.replace(month=month, day=1, hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=-1))
            s_now = now - relativedelta(months=3)
            s_now = get_last_day_in_month(s_now)

            def get_date_and_seasondate(c_time):
                date, seasondate = "", ""
                year = c_time.strftime("%Y")
                if c_time.month in (1, 2, 3):
                    season = '第1季度'
                    seasondate = year + '-' + season
                    date = year + '-' + "03-31"
                if c_time.month in (4, 5, 6):
                    season = '第2季度'
                    seasondate = year + '-' + season
                    date = year + '-' + "06-30"
                if c_time.month in (7, 8, 9):
                    season = '第3季度'
                    seasondate = year + '-' + season
                    date = year + '-' + "09-30"
                if c_time.month in (10, 11, 12):
                    season = '第4季度'
                    seasondate = year + '-' + season
                    date = year + '-' + "12-31"
                return date, seasondate

            e_date, e_seasondate = get_date_and_seasondate(now)
            s_date, s_seasondate = get_date_and_seasondate(s_now)

        e_yeardate = ''
        s_yeardate = ''
        if date_type == '13':  # 半年
            now = n_time
            month = (now.month - 1) - (now.month - 1) % 6 + 1
            now = (n_time.replace(month=month, day=1, hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=-1))
            s_now = now - relativedelta(months=6)
            s_now = get_last_day_in_month(s_now)

            def get_date_and_yeardate(c_time):
                date, yeardate = "", ""
                year = now.strftime("%Y")
                if now.month in (1, 2, 3, 4, 5, 6):
                    season = '上半年'
                    yeardate = year + '-' + season
                    date = year + '-' + "06-30"
                if now.month in (7, 8, 9, 10, 11, 12):
                    season = '下半年'
                    yeardate = year + '-' + season
                    date = year + '-' + "12-31"
                return date, yeardate

            e_date, e_yeardate = get_date_and_yeardate(now)
            s_date, s_yeardate = get_date_and_yeardate(s_now)
        if date_type == '14':  # 年
            now = (n_time.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=-1))
            s_now = now - relativedelta(months=12)
            s_now = get_last_day_in_month(s_now)

            e_date = now.strftime("%Y")
            s_date = s_now.strftime("%Y")

        search_name = ""
        try:
            search_name = TargetStatistic.objects.get(id=int(search_id)).name
        except Exception:
            pass

        return render(request, "statistic_report.html", locals())
    else:
        return HttpResponseRedirect("/login")


def get_statistic_report(request):
    """
    rowspan if_group 为 是 =2 否 = 1

    colspan	分组指标数

    [{"col_name": "", "rowspan": "", "colspan": "",  "targets": [{"name": ""}, {"name": ""}]}]
    # 同一时间点 所有指标的当前值
    [{"date": "2020-01-31", "target_values": []}, {"date": "2020-01-30", "target_values": []}]
    """
    if request.user.is_authenticated():
        start_date = request.POST.get("start_date", "")
        end_date = request.POST.get("end_date", "")
        search_id = request.POST.get("search_id", "")
        date_type = request.POST.get("date_type", "")

        # start_date = "2020-01-01"
        # end_date = "2020-01-31"
        # search_id = "1"

        data = {}
        status = 1
        info = ""

        head_data = [{
            "col_name": "指标数据时间",
            "rowspan": 2,
            "colspan": 1,
            "targets": []
        }]
        body_data = []
        v_sums = []  # 合计
        if not start_date:
            status = 0
            info = "开始时间未选择。"
        elif not end_date:
            status = 0
            info = "结束时间未选择。"
        elif not search_id:
            status = 0
            info = "当前页面已失效，请重新访问。"
        else:
            try:
                start_date = getreporting_date(start_date, date_type)
                end_date = getreporting_date(end_date, date_type)

                target_statistic = TargetStatistic.objects.get(id=int(search_id))
                col_data = target_statistic.col_data

                """
                "[{
                    'statistic_type': '1', 
                    'name': 'b', 
                    'remark': '', 
                    'targets': [
                        {'new_target_name': '#1运行时间', 'target_id': '1884', 'cumulative_type': '0', 'target_name': '#1运行时间'}, 
                        {'new_target_name': '#2运行时间', 'target_id': '1885', 'cumulative_type': '4', 'target_name': '#2运行时间'}
                    ]
                }]"
                """
                try:
                    col_data = eval(col_data)
                except Exception as e:
                    print(e)
                else:
                    """
                    [{'name': '列二', 'if_group': '否', 'remark': '列二的说明', 
                    'targets': [{'target_id': '21', 'target_name': '热力结算-日报-录入-002'}]}, 
                    
                    {'name': '列一', 'if_group': '是', 'remark': '列一的说明', 
                    'targets': [{'target_id': '21', 'new_target_name': '#1机组', 'target_name': '热力结算-日报-录入-002'}, 
                                {'target_id': '22', 'new_target_name': '#2机组', 'target_name': '热力结算-日报-录入-003'}]}]
                    """

                    # 指定时间段内 Calculatedata Extractdata Entrydata Meterdata所有数据
                    def get_target_values(operation_type, start_date, end_date, date_type):
                        """
                        获取指定时间内，不同操作类型的所有数据，包括隔年、跨年
                        :param operation_type:
                        :param start_date:
                        :param end_date:
                        :return:
                        """
                        data = []
                        model_map = {
                            "1": "Meterdata",
                            "15": "Entrydata",
                            "16": "Extractdata",
                            "17": "Calculatedata",
                        }

                        model_name = ""
                        try:
                            model_name = model_map[operation_type]
                        except Exception:
                            pass
                        if model_name:
                            target_val = []
                            # 判断开始时间与结束时间是否在同一年
                            start_date_year = start_date.year
                            end_date_year = end_date.year
                            delta_year = end_date_year - start_date_year
                            if delta_year == 0:  # 同一年
                                target_val = getmodels(model_name, str(start_date_year)).objects.exclude(state="9").filter(
                                    Q(datadate__gte=start_date.date()) & Q(datadate__lte=end_date.date())
                                ).values(
                                    "curvalue", "cumulativemonth", "cumulativequarter", "cumulativehalfyear", "cumulativeyear",
                                    "target_id", "datadate", "target__digit", "target__cycletype"
                                )

                            else:
                                # 开始时间到年底
                                start_target_val = getmodels(model_name, str(start_date_year)).objects.exclude(state="9").filter(datadate__gte=start_date.date()).values(
                                    "curvalue", "cumulativemonth", "cumulativequarter", "cumulativehalfyear", "cumulativeyear",
                                    "target_id", "datadate", "target__digit", "target__cycletype"
                                )

                                # 结束时间到年初
                                end_target_val = getmodels(model_name, str(end_date_year)).objects.exclude(state="9").filter(datadate__lte=end_date.date()).values(
                                    "curvalue", "cumulativemonth", "cumulativequarter", "cumulativehalfyear", "cumulativeyear",
                                    "target_id", "datadate", "target__digit", "target__cycletype"
                                )
                                target_val.extend(start_target_val)
                                target_val.extend(end_target_val)
                                # 2017 2019 2
                                if delta_year > 1:  # 隔年
                                    for i in range(0, delta_year):
                                        start_date_year += 1
                                        start_date = datetime.datetime(start_date_year, 1, 1)
                                        middle_target_val = getmodels(model_name, str(start_date_year)).objects.exclude(state="9").filter(datadate__gte=start_date.date()).values(
                                            "curvalue", "cumulativemonth", "cumulativequarter", "cumulativehalfyear", "cumulativeyear",
                                            "target_id", "datadate", "target__digit", "target__cycletype"
                                        )
                                        if middle_target_val:
                                            target_val.extend(middle_target_val)
                                else:  # 跨年
                                    pass
                            data = [{
                                "id": tv["target_id"],
                                "curvalue": float(round(tv["curvalue"] if tv["curvalue"] else 0, tv["target__digit"])),
                                "cumulativemonth": float(round(tv["cumulativemonth"] if tv["cumulativemonth"] else 0, tv["target__digit"])),
                                "cumulativequarter": float(round(tv["cumulativequarter"] if tv["cumulativequarter"] else 0, tv["target__digit"])),
                                "cumulativehalfyear": float(round(tv["cumulativehalfyear"] if tv["cumulativehalfyear"] else 0, tv["target__digit"])),
                                "cumulativeyear": float(round(tv["cumulativeyear"] if tv["cumulativeyear"] else 0, tv["target__digit"])),
                                "date": "{0:%Y-%m-%d}".format(tv["datadate"]) if tv["datadate"] else "",
                            } for tv in target_val if str(tv["target__cycletype"]) == date_type]
                        return sorted(data, key=lambda e: e.__getitem__('date'), reverse=True)

                    meter_data = get_target_values('1', start_date, end_date, date_type)
                    entry_data = get_target_values('15', start_date, end_date, date_type)
                    extract_data = get_target_values('16', start_date, end_date, date_type)
                    calculate_data = get_target_values('17', start_date, end_date, date_type)

                    all_data = {
                        "1": meter_data,
                        "15": entry_data,
                        "16": extract_data,
                        "17": calculate_data,
                    }

                    # head_data
                    for cd in col_data:
                        head_targets = []
                        col_name = cd["name"]
                        targets = cd["targets"]
                        colspan = len(targets)
                        if colspan > 1:
                            rowspan = 1
                        else:
                            rowspan = 2
                        for target in targets:
                            head_targets.append(target)

                        head_data.append({
                            "col_name": col_name,
                            "rowspan": rowspan,
                            "colspan": colspan,
                            "targets": head_targets
                        })

                    # body_data
                    # 时间列表
                    def get_date_list_during_period(start_time, end_time, date_type):
                        """
                        不同周期类型下，指定时间区间获取时间列表
                            日：每日
                            月：月最后一天
                            季：季最后一天
                            半年：半年最后一天
                            年：年最后一天
                        @param start_time:
                        @param end_time:
                        @param date_type:
                        @return date_list:
                        """
                        date_list = []

                        n = 0
                        n_time = end_time
                        if date_type == "10":
                            while True:
                                date_list.append(n_time)

                                n_time -= datetime.timedelta(days=1)

                                if n_time < start_time or n > 3 * 365:  # 最大循环
                                    break
                                n += 1
                        if date_type == "11":
                            while True:
                                date_list.append(n_time)

                                n_time -= relativedelta(months=1)
                                n_time = get_last_day_in_month(n_time)

                                if n_time < start_time or n > 3 * 365:
                                    break
                                n += 1
                        if date_type == "12":
                            while True:
                                date_list.append(n_time)

                                n_time -= relativedelta(months=3)
                                n_time = get_last_day_in_month(n_time)

                                if n_time < start_time or n > 3 * 365:
                                    break
                                n += 1
                        if date_type == "13":
                            while True:
                                date_list.append(n_time)

                                n_time -= relativedelta(months=6)
                                n_time = get_last_day_in_month(n_time)

                                if n_time < start_time or n > 3 * 365:
                                    break
                                n += 1
                        if date_type == "14":
                            while True:
                                date_list.append(n_time)

                                n_time -= relativedelta(months=12)
                                n_time = get_last_day_in_month(n_time)

                                if n_time < start_time or n > 2000:
                                    break
                                n += 1

                        return date_list

                    date_list = get_date_list_during_period(start_date, end_date, date_type)

                    all_targets = Target.objects.exclude(state="9").values(
                        "id", "name", "operationtype"
                    )

                    def get_target_info(target_id: str) -> dict:
                        target_info = {}
                        for t in all_targets:
                            if str(t['id']) == target_id:
                                target_info = t
                                break
                        return target_info

                    def handle_target_data(date):
                        target_values = []

                        for cd in col_data:
                            targets = cd["targets"]
                            statistic_type = cd["statistic_type"]
                            for target in targets:
                                target_id = target["target_id"]
                                operation_type = get_target_info(target_id).get("operationtype", "")
                                try:
                                    cur_data = all_data[operation_type]
                                except Exception:
                                    pass
                                else:
                                    has_value = False
                                    for d in cur_data:
                                        if str(d["id"]) == target_id and d["date"] == "{:%Y-%m-%d}".format(date):
                                            # 判断取的值类型
                                            if target["cumulative_type"] == "0":
                                                target_values.append({
                                                    "value": d["curvalue"],
                                                    "statistic_type": statistic_type,
                                                })
                                            if target["cumulative_type"] == "1":
                                                target_values.append({
                                                    "value": d["cumulativemonth"],
                                                    "statistic_type": statistic_type,
                                                })
                                            if target["cumulative_type"] == "2":
                                                target_values.append({
                                                    "value": d["cumulativequarter"],
                                                    "statistic_type": statistic_type,
                                                })
                                            if target["cumulative_type"] == "3":
                                                target_values.append({
                                                    "value": d["cumulativehalfyear"],
                                                    "statistic_type": statistic_type,
                                                })
                                            if target["cumulative_type"] == "4":
                                                target_values.append({
                                                    "value": d["cumulativeyear"],
                                                    "statistic_type": statistic_type,
                                                })
                                            has_value = True
                                            break
                                    if not has_value:
                                        target_values.append({
                                            "value": "-",
                                            "statistic_type": statistic_type,
                                        })
                        if target_values:
                            return {
                                "date": "{:%Y-%m-%d}".format(date),
                                "target_values": target_values
                            }

                    pool = ThreadPoolExecutor(max_workers=100)
                    all_tasks = [pool.submit(handle_target_data, date) for date in date_list]
                    for future in as_completed(all_tasks):
                        if future.result():
                            body_data.append(future.result())

                body_data = sorted(body_data, key=lambda e: e.__getitem__('date'), reverse=True)
                # 合计(判断求和/平均)
                if body_data:
                    target_values_length = len(body_data[0]["target_values"])
                    for i in range(0, target_values_length):
                        v_sum = decimal.Decimal('0')
                        statistic_type = ""
                        for bd in body_data:
                            target_values = bd["target_values"]
                            c_v = target_values[i].get("value", "-")
                            statistic_type = target_values[i].get("statistic_type", "-")
                            if type(c_v) != str:
                                v_sum += decimal.Decimal(str(c_v))
                        if statistic_type == "1":  # 求和
                            pass
                        if statistic_type == "2":  # 平均
                            v_sum = v_sum / len(body_data)
                            v_sum = round(v_sum, 4)
                        if statistic_type == "-":  # 无
                            v_sum = "-"
                        v_sums.append(float(v_sum) if v_sum else "-")

            except Exception as e:
                status = 0
                info = "获取报表数据失败{0}".format(e)
        return JsonResponse({
            "status": status,
            "info": info,
            "data": {
                "head_data": head_data,
                "body_data": body_data,
                "v_sums": v_sums,
            }
        })
    else:
        return HttpResponseRedirect("/login")


def electric_energy(request, funid):
    if request.user.is_authenticated():
        yestoday = "{:%Y-%m-%d}".format(datetime.datetime.now() - datetime.timedelta(days=1))

        return render(request, "electric_energy.html", {
            "yestoday": yestoday,
            "username": request.user.userinfo.fullname,
            "pagefuns": getpagefuns(funid, request)
        })
    else:
        return HttpResponseRedirect("/login")


def get_electric_energy_target_info():
    """
    获取发电量指标的相关信息，如保留位数
    :return:
    """
    f_info = {
        "digit": 2,
    }
    s_info = {
        "digit": 2,
    }
    F_ELERTRIC_ENERGY = settings.F_ELERTRIC_ENERGY
    S_ELERTRIC_ENERGY = settings.S_ELERTRIC_ENERGY

    f_targets = Target.objects.exclude(state="9").filter(code=F_ELERTRIC_ENERGY)

    if f_targets.exists():
        f_target = f_targets[0]
        f_info["digit"] = f_target.digit

    s_targets = Target.objects.exclude(state="9").filter(code=S_ELERTRIC_ENERGY)
    if s_targets:
        s_target = s_targets[0]
        s_info["digit"] = s_target.digit

    return f_info, s_info


def get_electric_energy(request):
    if request.user.is_authenticated():
        result = []

        # #1发电量 #2发电量 保留位数
        f_info, s_info = get_electric_energy_target_info()
        f_digit = f_info.get('digit', 2)
        s_digit = s_info.get('digit', 2)
        electric_energys = ElectricEnergy.objects.exclude(state="9").order_by("-extract_time")
        for electric_energy in electric_energys:
            f_electric_energy = float(round(electric_energy.f_electric_energy, f_digit)) if electric_energy.f_electric_energy else 0
            s_electric_energy = float(round(electric_energy.s_electric_energy, s_digit)) if electric_energy.s_electric_energy else 0
            result.append({
                "id": electric_energy.id,
                "extract_time": "{0:%Y-%m-%d}".format(electric_energy.extract_time) if electric_energy.extract_time else "",
                "f_electric_energy": f_electric_energy,
                "s_electric_energy": s_electric_energy,
                "a_electric_energy": round(f_electric_energy + s_electric_energy, f_digit),
            })
        return JsonResponse({
            "data": result
        })
    else:
        return HttpResponseRedirect("/login")


def save_electric_energy(request):
    if request.user.is_authenticated():
        status = 1
        info = "保存成功。"
        f_electric_energy = request.POST.get("f_electric_energy", "")
        s_electric_energy = request.POST.get("s_electric_energy", "")
        extract_time = request.POST.get("extract_time", "")
        f_is_open = request.POST.get("f_is_open", "")
        s_is_open = request.POST.get("s_is_open", "")

        f_electric_energy = decimal.Decimal(f_electric_energy if f_electric_energy else "0")
        s_electric_energy = decimal.Decimal(s_electric_energy if s_electric_energy else "0")

        # 未启动
        if f_is_open == "0":
            f_electric_energy = decimal.Decimal("0")
        if s_is_open == "0":
            s_electric_energy = decimal.Decimal("0")

        a_electric_energy = f_electric_energy + s_electric_energy

        try:
            extract_time = datetime.datetime.strptime(extract_time, "%Y-%m-%d")
        except ValueError as e:
            print(e)
            info = "网络异常。"
            status = 0
        else:
            with transaction.atomic():
                # 删除该天其他数据
                ElectricEnergy.objects.filter(extract_time=extract_time).update(**{
                    "state": "9"
                })

                ElectricEnergy.objects.create(**{
                    "f_electric_energy": f_electric_energy,
                    "s_electric_energy": s_electric_energy,
                    "a_electric_energy": a_electric_energy,
                    "extract_time": extract_time,
                })

        return JsonResponse({
            "status": status,
            "info": info,
        })
    else:
        return HttpResponseRedirect("/login")


def electric_energy_del(request):
    if request.user.is_authenticated():
        status = 1
        info = '删除成功。'
        id = request.POST.get('id', '')
        try:
            ElectricEnergy.objects.filter(id=int(id)).update(**{
                "state": "9"
            })
        except:
            status = 0
            info = '删除失败。'

        return JsonResponse({
            'status': status,
            'info': info
        })
    else:
        return HttpResponseRedirect("/login")


def extract_electric_energy(request):
    """
    手动提取指定时间段的发电量
    @param request:
    @return:
    """
    if request.user.is_authenticated():
        status = 1
        info = '提取成功。'
        data = {}

        def check_time(start_time, end_time):
            """
            检测时间
            @param start_time:
            @param end_time:
            @return is_fine:
            """
            is_fine = True
            err = ''
            if not start_time:
                is_fine = False
                err = "开始时间未选择"
            elif not end_time:
                is_fine = False
                err = "结束时间未选择"
            else:
                start_time = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
                end_time = datetime.datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
                if start_time > end_time:
                    is_fine = False
                    err = "开始时间不得晚于结束时间"
            return is_fine, err

        def do_extract(start_time, end_time, f=True):
            """
            #1机组 #2机组 发电量取数
            @param start_time:
            @param end_time:
            @param f: f表示#1机组 s表示#2机组
            @return: electric_energy_value
            """
            electric_energy_value = 0

            if f:  # #1
                t_code = settings.F_ELERTRIC_ENERGY
                t_tag = settings.F_TAG
            else:  # #2
                t_code = settings.S_ELERTRIC_ENERGY
                t_tag = settings.S_TAG

            ts = Target.objects.exclude(state="9").filter(code=t_code)
            if ts.exists():
                t = ts[0]

                s_con = settings.PI_SERVER

                if s_con:
                    try:
                        s_con = eval(s_con)
                        if type(s_con) == list:
                            s_con = s_con[0]
                    except Exception as e:
                        pass
                    else:
                        pi_query = PIQuery(s_con)
                        result, err = pi_query.get_delta_time_data(start_time, end_time, t, t_tag)
                        if not err and result:
                            electric_energy_value = result[0][0]
            return electric_energy_value

        f_checkbox = request.POST.get('f_checkbox', '')
        s_checkbox = request.POST.get('s_checkbox', '')

        f_start_time1 = request.POST.get('f_start_time1', '')
        f_start_time2 = request.POST.get('f_start_time2', '')
        f_start_time3 = request.POST.get('f_start_time3', '')
        f_start_time4 = request.POST.get('f_start_time4', '')

        f_end_time1 = request.POST.get('f_end_time1', '')
        f_end_time2 = request.POST.get('f_end_time2', '')
        f_end_time3 = request.POST.get('f_end_time3', '')
        f_end_time4 = request.POST.get('f_end_time4', '')

        s_start_time1 = request.POST.get('s_start_time1', '')
        s_start_time2 = request.POST.get('s_start_time2', '')
        s_start_time3 = request.POST.get('s_start_time3', '')
        s_start_time4 = request.POST.get('s_start_time4', '')

        s_end_time1 = request.POST.get('s_end_time1', '')
        s_end_time2 = request.POST.get('s_end_time2', '')
        s_end_time3 = request.POST.get('s_end_time3', '')
        s_end_time4 = request.POST.get('s_end_time4', '')

        f_electric_energy = decimal.Decimal("0")
        s_electric_energy = decimal.Decimal("0")
        if f_checkbox == "on":
            if not any([f_start_time1, f_start_time2, f_start_time3, f_start_time4,
                        f_end_time1, f_end_time2, f_end_time3, f_end_time4]):
                return JsonResponse({
                    'status': 0,
                    'info': '开机状态时，#1机组入网时间至少要选择一组。'
                })

            if any([f_start_time1, f_end_time1]):
                is_fine, err = check_time(f_start_time1, f_end_time1)
                if not is_fine:
                    return JsonResponse({
                        'status': 0,
                        'info': '提取失败，#1机组入网时间1{0}。'.format(err),
                    })
                else:
                    f_electric_energy += do_extract(f_start_time1, f_end_time1, f=True)
            if any([f_start_time2, f_end_time2]):
                is_fine, err = check_time(f_start_time2, f_end_time2)
                if not is_fine:
                    return JsonResponse({
                        'status': 0,
                        'info': '提取失败，#1机组入网时间2{0}。'.format(err),
                    })
                else:
                    f_electric_energy += do_extract(f_start_time2, f_end_time2, f=True)
            if any([f_start_time3, f_end_time3]):
                is_fine, err = check_time(f_start_time3, f_end_time3)
                if not is_fine:
                    return JsonResponse({
                        'status': 0,
                        'info': '提取失败，#1机组入网时间3{0}。'.format(err),
                    })
                else:
                    f_electric_energy += do_extract(f_start_time3, f_end_time3, f=True)
            if any([f_start_time4, f_end_time4]):
                is_fine, err = check_time(f_start_time4, f_end_time4)
                if not is_fine:
                    return JsonResponse({
                        'status': 0,
                        'info': '提取失败，#1机组入网时间4{0}。'.format(err),
                    })
                else:
                    f_electric_energy += do_extract(f_start_time4, f_end_time4, f=True)
        if s_checkbox == "on":
            if not any([s_start_time1, s_start_time2, s_start_time3, s_start_time4,
                        s_end_time1, s_end_time2, s_end_time3, s_end_time4]):
                return JsonResponse({
                    'status': 0,
                    'info': '开机状态时，#2机组入网时间至少要选择一组。'
                })
            if any([s_start_time1, s_end_time1]):
                is_fine, err = check_time(s_start_time1, s_end_time1)
                if not is_fine:
                    return JsonResponse({
                        'status': 0,
                        'info': '提取失败，#2机组入网时间1{0}。'.format(err),
                    })
                else:
                    s_electric_energy += do_extract(s_start_time1, s_end_time1, f=False)
            if any([s_start_time2, s_end_time2]):
                is_fine, err = check_time(s_start_time2, s_end_time2)
                if not is_fine:
                    return JsonResponse({
                        'status': 0,
                        'info': '提取失败，#2机组入网时间2{0}。'.format(err),
                    })
                else:
                    s_electric_energy += do_extract(s_start_time2, s_end_time2, f=False)
            if any([s_start_time3, s_end_time3]):
                is_fine, err = check_time(s_start_time3, s_end_time3)
                if not is_fine:
                    return JsonResponse({
                        'status': 0,
                        'info': '提取失败，#2机组入网时间3{0}。'.format(err),
                    })
                else:
                    s_electric_energy += do_extract(s_start_time3, s_end_time3, f=False)
            if any([s_start_time4, s_end_time4]):
                is_fine, err = check_time(s_start_time4, s_end_time4)
                if not is_fine:
                    return JsonResponse({
                        'status': 0,
                        'info': '提取失败，#2机组入网时间4{0}。'.format(err),
                    })
                else:
                    s_electric_energy += do_extract(s_start_time4, s_end_time4, f=False)

        return JsonResponse({
            'status': status,
            'info': info,
            'data': {
                'f_electric_energy': float(f_electric_energy),
                's_electric_energy': float(s_electric_energy)
            },
        })
    else:
        return HttpResponseRedirect("/login")
