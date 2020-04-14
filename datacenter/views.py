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

from datacenter.tasks import *
from .models import *
from .remote import ServerByPara
from ZDDC import settings
from .funcs import *
from .ftp_file_handler import *
from utils.handle_process import Extract

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


def remove_decimal(num):
    """
    移除小数点后多余的0
    """
    return num.to_integral() if num == num.to_integral() else num.normalize()


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
    else:
        digit = '0.00000'
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
        circle_id = request.POST.get('circle_id', '')
        app_id = request.POST.get('app_id', '')
        source_id = request.POST.get('source_id', '')
        index = request.POST.get('index', '')
        try:
            circle_id = int(circle_id)
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

        s_info_list = []
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
                                        'type': 'circle',

                                        # 主进程id
                                        'cp_id': cp_id,

                                        # 进程状态
                                        'create_time': create_time,
                                        'last_time': last_time,
                                        'status': status
                                    }

                                    c_info['state'] = {'opened': True}
                                    #
                                    if circle_id == c.id and app_id == a.id and source_id == s.id:
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

                    s_info_list.append(s_info)
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
                s_info_list.append(fixed_s_info)

        root_info['children'] = s_info_list
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
        for process_monitor in process_monitors:
            p_id = process_monitor.p_id
            try:
                p_id = int(p_id)
            except ValueError as e:
                process_monitor.status = "已关闭"
                process_monitor.create_time = None
                process_monitor.save()
            else:
                py_process = check_py_exists(p_id)
                if not py_process:
                    process_monitor.status = "已关闭"
                    process_monitor.create_time = None
                    process_monitor.p_id = ""
                    process_monitor.save()

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


def create_process(request):
    """
    修改数据源
    :param request:
    :return:
    """
    if request.user.is_authenticated():
        process_id = request.POST.get("id", "")
        name = request.POST.get("name", "")
        code = request.POST.get("code", "")
        source_type = request.POST.get("sourcetype", "")
        try:
            process_id = int(process_id)
        except:
            raise Http404()
        result = {}

        if code.strip() == '':
            result["res"] = '数据源代码不能为空。'
        else:
            if name.strip() == '':
                result["res"] = '数据源名称不能为空。'
            else:
                if source_type.strip() == '':
                    result["res"] = '数据源类型不能为空。'
                else:
                    try:
                        source = Source.objects.filter(id=process_id)
                        if source.exists():
                            source = source[0]
                            source.name = name
                            source.code = code
                            source.sourcetype = source_type
                            source.save()
                            result["res"] = "保存成功。"
                    except Exception as e:
                        print(e)
                        result["res"] = "保存失败。"

        return JsonResponse(result)


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
        circle_id = request.POST.get("circle_id", "")
        operate = request.POST.get("operate", "")
        check_type = request.POST.get("check_type", "")
        try:
            source_id = int(source_id)
            app_id = int(app_id)
            circle_id = int(circle_id)
        except ValueError as e:
            print(e)

        # 进程操作记入日志
        def record_log(app_id, source_id, circle_id, msg):
            try:
                log = LogInfo()
                log.source_id = source_id
                log.app_id = app_id
                log.cycle_id = circle_id
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
                cycle_id=circle_id).exclude(state='9')

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
                    record_log(app_id, source_id, circle_id, '进程启动成功。')
            elif operate == 'stop':
                if current_process.status != "运行中":
                    tag = 0
                    res = "当前进程未在运行中。"
                else:
                    tag, res = handle_process(current_process, handle_type="DESTROY")
                    record_log(app_id, source_id, circle_id, '进程关闭成功。')
            elif operate == 'restart':
                if current_process.status != "运行中":
                    tag = 0
                    res = "当前进程未在运行中，请启动程序。"
                else:
                    tag, res = handle_process(current_process, handle_type="DESTROY")
                    if tag == 1:
                        tag, res = handle_process(current_process, handle_type="RUN")
                        record_log(app_id, source_id, circle_id, '进程重启成功。')
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
                current_process.cycle_id = circle_id
            current_process.save()
            tag, res = handle_process(current_process, handle_type="RUN")
            record_log(app_id, source_id, circle_id, '进程启动成功。')
            return JsonResponse({
                'tag': tag,
                'res': res,
                'data': ''
            })


def process_destroy(request):
    if request.user.is_authenticated():
        p_id = request.POST.get("id", "")
        current_process = Source.objects.filter(id=p_id).exclude(
            status__in=["已关闭", "", "进程异常关闭，请重新启动。"]).exclude(state="9")
        result = {}
        if current_process.exists():
            # 异步开启程序
            tag, res = handle_process(p_id, handle_type="DESTROY")
            result["tag"] = tag
            result["res"] = res
        else:
            result["tag"] = 0
            result["res"] = "该程序未运行。"
        return JsonResponse(result)


def pm_target_data(request):
    """
    根据应用、数据源、周期 过滤出所有指标
    :param request:
    :return:
    """
    if request.user.is_authenticated():
        app_id = request.GET.get('app_id', '')
        source_id = request.GET.get('source_id', '')
        circle_id = request.GET.get('circle_id', '')

        result = []

        supplement_status = '0'  # 1启动成功 0完成 2失败
        try:
            app_id = int(app_id)
            source_id = int(source_id)
            circle_id = int(circle_id)
        except ValueError as e:
            print(e)
        else:
            targets = Target.objects.exclude(state='9').filter(
                Q(adminapp_id=app_id) & Q(source_id=source_id) & Q(cycle_id=circle_id))

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
                                                                                cycle_id=circle_id)
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
        circle_id = request.GET.get('circle_id', '')

        try:
            app_id = int(app_id)
            source_id = int(source_id)
            circle_id = int(circle_id)
        except ValueError as e:
            print(e)
        else:
            exceptions = ExceptionData.objects.filter(app_id=app_id, source_id=source_id, cycle_id=circle_id).exclude(
                state=9)
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


def get_log_info(request):
    if request.user.is_authenticated():
        result = []
        app_id = request.GET.get('app_id', '')
        source_id = request.GET.get('source_id', '')
        circle_id = request.GET.get('circle_id', '')

        try:
            app_id = int(app_id)
            source_id = int(source_id)
            circle_id = int(circle_id)
        except ValueError as e:
            print(e)
        else:
            log_infos = LogInfo.objects.filter(
                Q(app_id=app_id) & Q(source_id=source_id) & Q(cycle_id=circle_id)).order_by('-create_time')

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
        selectedtarget = request.POST.getlist('selectedtarget[]', [])
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

            targets = Target.objects.filter(id__in=selectedtarget)
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
        print(result)
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
                circle_name = pm.cycle.name if pm.cycle else ''
                status = pm.status
                create_time = '{:%Y-%m-%d %H:%M:%S}'.format(pm.create_time) if pm.create_time else ''
                last_time = '{:%Y-%m-%d %H:%M:%S}'.format(pm.last_time) if pm.last_time else ''

                result['data'] = {
                    'source_name': source_name,
                    'source_code': source_code,
                    'source_type': source_type,
                    'app_name': app_name,
                    'circle_name': circle_name,
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
                                                            try:
                                                                cur_app = App.objects.get(id=int(app))
                                                            except:
                                                                write_tag = False
                                                                errors.append('应用不存在。')
                                                            else:
                                                                app_code = cur_app.code
                                                                aft_report_file_path = os.path.join(rs.report_file_path, str(app_code))
                                                                report_check_cmd = r'if not exist {report_file_path} md {report_file_path}'.format(
                                                                    report_file_path=aft_report_file_path)
                                                                rc = ServerByPara(report_check_cmd, remote_ip, remote_user,
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
                                                                            ps_script_path, os.path.join(aft_report_file_path, file_name), url_visited)

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
                                                        report_save = ReportModel.objects.get(
                                                            id=id)
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
                                    errors.append('报表类别不能为空。')
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
                                                                aft_report_file_path = os.path.join(rs.report_file_path, str(app_code))
                                                                report_check_cmd = r'if not exist {report_file_path} md {report_file_path}'.format(
                                                                    report_file_path=aft_report_file_path)

                                                            rc = ServerByPara(report_check_cmd, remote_ip, remote_user,
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
                                                                        ps_script_path, os.path.join(aft_report_file_path, file_name), url_visited)

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
                                                        report_save = ReportModel.objects.get(
                                                            id=id)
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

        all_report = ReportModel.objects.exclude(state="9").order_by("sort")
        if search_app != "":
            curadminapp = App.objects.get(id=int(search_app))
            all_report = all_report.filter(app=curadminapp)

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
                "app": report.app.name,
                "app_id": report.app.id,
                "report_type_num": report.report_type,
                "sort": report.sort,
                "report_info_list": report_info_list,
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

        all_app = App.objects.exclude(state="9").order_by("sort")
        for app in all_app:
            # 应用对应的所有业务
            works = app.work_set.exclude(state='9').order_by('sort')

            work_list = []

            for work in works:
                tmp_list = [work.id, work.name, work.code, work.remark, work.core, work.sort]
                work_list.append(tmp_list)

            result.append({
                "id": app.id,
                "name": app.name,
                "code": app.code,
                "remark": app.remark,
                "sort": app.sort,
                "works": json.dumps(work_list, ensure_ascii=False),
            })

        return JsonResponse({"data": result})


def dictindex(request, funid):
    if request.user.is_authenticated():
        try:
            curfun = Fun.objects.get(id=int(funid))
            if curfun in funlist:
                alldict = DictIndex.objects.order_by("sort").exclude(state="9")
                return render(request, 'dict.html',
                              {'username': request.user.userinfo.fullname,
                               "alldict": alldict, "pagefuns": getpagefuns(funid)})
            else:
                return HttpResponseRedirect("/index")
        except:
            return HttpResponseRedirect("/index")
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

        c_dict_index_1 = DictIndex.objects.filter(
            id=4).exclude(state='9')
        if c_dict_index_1.exists():
            c_dict_index_1 = c_dict_index_1[0]
            dict_list1 = c_dict_index_1.dictlist_set.exclude(state="9")
            for i in dict_list1:
                storage_type_list.append({
                    "storage_name": i.name,
                    "storage_type_id": i.id,
                })

        c_dict_index_2 = DictIndex.objects.filter(
            id=3).exclude(state='9')
        if c_dict_index_2.exists():
            c_dict_index_2 = c_dict_index_2[0]
            dict_list2 = c_dict_index_2.dictlist_set.exclude(state="9")
            for i in dict_list2:
                valid_time_list.append({
                    "valid_time": i.name,
                    "valid_time_id": i.id,
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

            storagetype = storage.validtime
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
            minutes = cycle.minute
            hours = cycle.hour
            per_week = cycle.day_of_week
            per_month = cycle.day_of_month
            schedule_type = cycle.schedule_type
            schedule_type_display = cycle.get_schedule_type_display()

            result.append({
                "id": cycle.id,
                "name": cycle.name,
                "sort": cycle.sort,

                "minutes": minutes,
                "hours": hours,
                "per_week": per_week,
                "per_month": per_month,
                "schedule_type": schedule_type,
                "schedule_type_display": schedule_type_display,
            })

        return JsonResponse({"data": result})


def cycle_save(request):
    if request.user.is_authenticated():
        id = request.POST.get("id", "")
        cycle_name = request.POST.get("cycle_name", "")
        sort = request.POST.get("sort", "")

        schedule_type = request.POST.get('schedule_type', '')

        per_time = request.POST.get('per_time', '')
        per_month = request.POST.get('per_month', '')
        per_week = request.POST.get('per_week', '')
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
            else:
                if schedule_type == 2:
                    if not per_week:
                        return JsonResponse({
                            "res": "周几未选择。"
                        })

                if schedule_type == 3:
                    if not per_month:
                        return JsonResponse({
                            "res": "每月第几天未选择。"
                        })

            hour, minute = per_time.split(':')
            if id == 0:
                all_cycle = Cycle.objects.filter(
                    name=cycle_name).exclude(state="9")
                if (len(all_cycle) > 0):
                    result["res"] = '存储代码:' + cycle_name + '已存在。'
                else:
                    cycle_save = Cycle()
                    cycle_save.name = cycle_name
                    cycle_save.hour = hour
                    cycle_save.minute = minute
                    cycle_save.day_of_week = per_week
                    cycle_save.day_of_month = per_month
                    cycle_save.schedule_type = schedule_type
                    cycle_save.sort = int(sort) if sort else None
                    cycle_save.save()
                    result["res"] = "保存成功。"
                    result["data"] = cycle_save.id
            else:
                all_cycle = Cycle.objects.filter(name=cycle_name).exclude(
                    id=id).exclude(state="9")
                if (len(all_cycle) > 0):
                    result["res"] = '存储名称:' + cycle_name + '已存在。'
                else:
                    try:
                        # 保存定时任务
                        cycle_save = Cycle.objects.get(id=id)
                        cycle_save.name = cycle_name
                        cycle_save.hour = hour
                        cycle_save.minute = minute
                        cycle_save.day_of_week = per_week
                        cycle_save.day_of_month = per_month
                        cycle_save.schedule_type = schedule_type
                        cycle_save.sort = int(
                            sort) if sort else None
                        cycle_save.save()
                        result["res"] = "保存成功。"
                        result["data"] = cycle_save.id
                    except Exception as e:
                        print(e)
                        result["res"] = "修改失败。"
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


def get_select_source_type(temp_source_type=""):
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
                       "pagefuns": getpagefuns(funid)})
    else:
        return HttpResponseRedirect("/login")


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

        all_target = Target.objects.exclude(state="9").order_by("sort").select_related("adminapp", "storage", "work")
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
        if search_app_noselect != "":
            curadminapp = App.objects.get(id=int(search_app_noselect))
            curapp = App.objects.filter(id=int(search_app_noselect))
            all_target = all_target.exclude(adminapp=curadminapp).exclude(app__in=curapp)

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
            admin_app = target.adminapp
            works = []
            if admin_app:
                works = admin_app.work_set.exclude(state='9').values('id', 'name')
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
                "upperlimit": target.upperlimit,
                "lowerlimit": target.lowerlimit,
                "formula": target.formula,
                "cycle": target.cycle_id,
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
                'works': str(works),
                "unity": target.unity,
                "is_repeat": target.is_repeat,
                "data_from": target.data_from
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

        all_app = App.objects.exclude(state="9")
        all_cycle = Cycle.objects.exclude(state="9")
        all_source = Source.objects.exclude(state="9").filter(type='')
        all_storage = Storage.objects.exclude(state="9")

        try:
            id = int(id)
        except:
            raise Http404()

        result = {}

        if name.strip() == '':
            result["res"] = '指标名称不能为空。'
        else:
            if code.strip() == '':
                result["res"] = '指标代码不能为空。'
            else:
                if operationtype.strip() == '':
                    result["res"] = '操作类型不能为空。'
                else:
                    if cycletype.strip() == '':
                        result["res"] = '周期类型不能为空。'
                    else:
                        if businesstype.strip() == '':
                            result["res"] = '业务类型不能为空。'
                        else:
                            if unit.strip() == '':
                                result["res"] = '机组不能为空。'
                            else:
                                if datatype.strip() == '':
                                    result["res"] = '数据类型不能为空。'
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

                                                if datatype == 'date' or datatype == 'text':
                                                    magnification = request.POST.get("")
                                                    digit = request.POST.get("")
                                                    upperlimit = request.POST.get("")
                                                    lowerlimit = request.POST.get("")
                                                    cumulative = request.POST.get("")
                                                    try:
                                                        target_save.magnification = magnification
                                                    except:
                                                        pass
                                                    try:
                                                        target_save.digit = digit
                                                    except:
                                                        pass
                                                    try:
                                                        target_save.upperlimit = upperlimit
                                                    except:
                                                        pass
                                                    try:
                                                        target_save.lowerlimit = lowerlimit
                                                    except:
                                                        pass
                                                    target_save.cumulative = cumulative
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
                                                    try:
                                                        cycle_id = int(cycle)
                                                        my_cycle = all_cycle.get(id=cycle_id)
                                                        target_save.cycle = my_cycle
                                                    except:
                                                        pass
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
                                        all_target = Target.objects.filter(code=code).exclude(id=id).exclude(state="9")
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
                                                    if datatype == 'date' or datatype == 'text':
                                                        magnification = request.POST.get("")
                                                        digit = request.POST.get("")
                                                        upperlimit = request.POST.get("")
                                                        lowerlimit = request.POST.get("")
                                                        cumulative = request.POST.get("")
                                                        try:
                                                            target_save.magnification = magnification
                                                        except:
                                                            pass
                                                        try:
                                                            target_save.digit = digit
                                                        except:
                                                            pass
                                                        try:
                                                            target_save.upperlimit = upperlimit
                                                        except:
                                                            pass
                                                        try:
                                                            target_save.lowerlimit = lowerlimit
                                                        except:
                                                            pass
                                                        target_save.cumulative = cumulative
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
                                                        try:
                                                            cycle_id = int(cycle)
                                                            my_cycle = all_cycle.get(id=cycle_id)
                                                            target_save.cycle = my_cycle
                                                        except:
                                                            pass
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
        adminapp = ""
        try:
            cur_fun = Fun.objects.filter(id=int(funid)).exclude(state='9')
            adminapp = cur_fun[0].app
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
        selectedtarget = request.POST.getlist('selectedtarget[]')

        result = {}
        try:
            app_id = int(adminapp)
        except:
            result["res"] = '数据异常，请重新打开页面。'
        my_app = App.objects.exclude(state="9").filter(id=app_id)
        if len(my_app) > 0:
            curapp = my_app[0]
            for target in selectedtarget:
                try:
                    my_target = Target.objects.exclude(state="9").get(id=int(target))
                    my_target.adminapp = curapp
                    my_target.save()
                except:
                    pass
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
                       "pagefuns": getpagefuns(funid)})
    else:
        return HttpResponseRedirect("/login")


def target_importapp(request):
    if request.user.is_authenticated():
        adminapp = request.POST.get("adminapp", "")
        selectedtarget = request.POST.getlist('selectedtarget[]')

        result = {}
        try:
            app_id = int(adminapp)
        except:
            result["res"] = '数据异常，请重新打开页面。'
        my_app = App.objects.exclude(state="9").filter(id=app_id)
        if len(my_app) > 0:
            curapp = my_app[0]
            for target in selectedtarget:
                try:
                    my_target = Target.objects.exclude(state="9").get(id=int(target))
                    my_target.app.add(curapp)
                    my_target.save()
                except:
                    pass
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
            value = remove_decimal(decimal.Decimal(constant.value))

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
                                all_constant = Constant.objects.filter(name=name).exclude(state="9")
                                if (len(all_constant) > 0):
                                    result["res"] = '常数名称:' + name + '已存在。'
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
                                all_constant = Constant.objects.filter(name=name).exclude(id=id).exclude(state="9")
                                if (len(all_constant) > 0):
                                    result["res"] = '常数名称:' + name + '已存在。'
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
                    (Q(app__in=curapp) & ~Q(adminapp_id=app)) | (Q(adminapp_id=app) & ~Q(work__core='是')))
            else:
                search_target = None
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

            if search_target is None or len(search_target) <= 0:
                searchtag = "display: none;"
            else:
                for target in search_target:
                    if target.adminapp is not None:
                        works = target.adminapp.work_set.exclude(state='9', id=work.id)

                        works_list = [
                            {"id": work.id, "name": work.name} for work in works if work.target_set.exclude(state='9').
                                filter(cycletype=cycletype).
                                filter(
                                (Q(app__in=curapp) & ~Q(adminapp_id=app)) | (Q(adminapp_id=app) & ~Q(work__core='是'))).
                                exists()
                        ]

                        # 数据查询的业务下拉框过滤掉没指标的项
                        cursearchapp = {
                            "id": target.adminapp.id,
                            "name": target.adminapp.name,
                            'works': works_list,
                        }
                        check_cursearchapp = {
                            "id": target.adminapp.id,
                            "name": target.adminapp.name,
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
                if data.target.cumulative == '是':

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
                    zerodata = data.zerodata
                    twentyfourdata = data.twentyfourdata
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

                    all_changedata = Meterchangedata.objects.exclude(state="9").filter(meterdata=data.id,
                                                                                       datadate=reporting_date)
                    if len(all_changedata) > 0:
                        meterchangedata_id = all_changedata[0].id
                        oldtable_zerodata = all_changedata[0].oldtable_zerodata
                        oldtable_twentyfourdata = all_changedata[0].oldtable_twentyfourdata
                        oldtable_value = all_changedata[0].oldtable_value
                        oldtable_magnification = all_changedata[0].oldtable_magnification
                        oldtable_finalvalue = all_changedata[0].oldtable_finalvalue
                        newtable_zerodata = all_changedata[0].newtable_zerodata
                        newtable_twentyfourdata = all_changedata[0].newtable_twentyfourdata
                        newtable_value = all_changedata[0].newtable_value
                        newtable_magnification = all_changedata[0].newtable_magnification
                        newtable_finalvalue = all_changedata[0].newtable_finalvalue
                        finalvalue = all_changedata[0].finalvalue
                        if data.target.cumulative == '是':
                            try:
                                oldtable_zerodata = round(data.oldtable_zerodata, data.target.digit)
                            except:
                                pass
                            try:
                                oldtable_twentyfourdata = round(data.oldtable_twentyfourdata, data.target.digit)
                            except:
                                pass
                            try:
                                oldtable_value = round(data.oldtable_value, data.target.digit)
                            except:
                                pass
                            try:
                                oldtable_magnification = round(data.oldtable_magnification, data.target.digit)
                            except:
                                pass
                            try:
                                oldtable_finalvalue = round(data.oldtable_finalvalue, data.target.digit)
                            except:
                                pass
                            try:
                                newtable_zerodata = round(data.newtable_zerodata, data.target.digit)
                            except:
                                pass
                            try:
                                newtable_twentyfourdata = round(data.newtable_twentyfourdata, data.target.digit)
                            except:
                                pass
                            try:
                                newtable_value = round(data.newtable_value, data.target.digit)
                            except:
                                pass
                            try:
                                newtable_magnification = round(data.newtable_magnification, data.target.digit)
                            except:
                                pass
                            try:
                                newtable_finalvalue = round(data.newtable_finalvalue, data.target.digit)
                            except:
                                pass
                            try:
                                finalvalue = round(data.finalvalue, data.target.digit)
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
            if data["target"].cumulative == '是':
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
        lastg_date = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(
            days=-1)
    if target.cycletype == "12":
        month = (date.month - 1) - (date.month - 1) % 3 + 1  # 10
        newdate = datetime.datetime(date.year, month, 1)
        lastg_date = newdate + datetime.timedelta(days=-1)
    if target.cycletype == "13":
        month = (date.month - 1) - (date.month - 1) % 6 + 1  # 10
        newdate = datetime.datetime(date.year, month, 1)
        lastg_date = newdate + datetime.timedelta(days=-1)
    if target.cycletype == "14":
        lastg_date = date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(
            days=-1)

    all_data = []
    if target.operationtype == "1":
        all_data = getmodels("Meterdata", str(lastg_date.year)).objects.exclude(state="9").filter(target=target,
                                                                                                  datadate=lastg_date)
    if target.operationtype == "15":
        all_data = getmodels("Entrydata", str(lastg_date.year)).objects.exclude(state="9").filter(target=target,
                                                                                                  datadate=lastg_date)
    if target.operationtype == "16":
        all_data = getmodels("Extractdata", str(lastg_date.year)).objects.exclude(state="9").filter(target=target,
                                                                                                    datadate=lastg_date)
    if target.operationtype == "17":
        all_data = getmodels("Calculatedata", str(lastg_date.year)).objects.exclude(state="9").filter(target=target,
                                                                                                      datadate=lastg_date)
    if len(all_data) > 0:
        lastcumulativemonth = 0
        lastcumulativequarter = 0
        lastcumulativehalfyear = 0
        lastcumulativeyear = 0
        try:
            if lastg_date.year == date.year and lastg_date.month == date.month:
                lastcumulativemonth += all_data[0].cumulativemonth
        except:
            pass
        try:
            if lastg_date.year == date.year and (lastg_date.month - 1) - (lastg_date.month - 1) % 3 == (
                    date.month - 1) - (date.month - 1) % 3:
                lastcumulativequarter += all_data[0].cumulativequarter
        except:
            pass
        try:
            if lastg_date.year == date.year and (lastg_date.month - 1) - (lastg_date.month - 1) % 6 == (
                    date.month - 1) - (date.month - 1) % 6:
                lastcumulativehalfyear += all_data[0].cumulativehalfyear
        except:
            pass
        try:
            if lastg_date.year == date.year:
                lastcumulativeyear += all_data[0].cumulativeyear
        except:
            pass
        cumulativemonth = lastcumulativemonth + value
        cumulativequarter = lastcumulativequarter + value
        cumulativehalfyear = lastcumulativehalfyear + value
        cumulativeyear = lastcumulativeyear + value
    return {"cumulativemonth": cumulativemonth, "cumulativequarter": cumulativequarter,
            "cumulativehalfyear": cumulativehalfyear, "cumulativeyear": cumulativeyear}


def getcalculatedata(target, date, guid,all_constant,all_target,tableList):
    """
    数据计算
    """

    if target.data_from == 'et':
        # 外部系统，直接取数
        # 从数据库中获取，取第一个值，其他情况抛错
        ret = Extract.getDataFromSource(target, datetime.datetime.now())
        if ret['result']:
            try:
                curvalue = float(ret['result'][0][0])
            except Exception as e:
                print(e)
                raise Exception('获取外部系统数据失败。')
            else:
                pass
        else:
            raise Exception('获取外部系统数据失败。')
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
                    # 公式中取常数值，不存在则去指标值
                    value = ""
                    isconstant=False
                    for constant in all_constant:
                        if membertarget==constant.code:
                            value = constant.value
                            isconstant = True
                            break
                    if not isconstant:
                        istarget = False
                        newtarget = None
                        for new_target in all_target:
                            if membertarget == new_target.code:
                                istarget = True
                                newtarget=new_target
                                break
                        if not istarget or newtarget is None:
                            formula = "-9999"
                            break
                        else:
                            # 同一应用，同一周期，同一业务，计算操作类型，guid不同(未计算过)的指标，先计算
                            # 即：当前指标由另一个公式中其他指标计算所得，'其他'指标值未计算出结果，先计算
                            #     A = B + 1 B未计算出，先计算出B
                            membertarget = newtarget
                            if membertarget.operationtype == target.operationtype and membertarget.adminapp_id == target.adminapp_id \
                                    and membertarget.cycletype == target.cycletype and membertarget.work_id == target.work_id \
                                    and membertarget.calculateguid != guid:
                                getcalculatedata(membertarget, date, guid,all_constant,all_target,tableList)

                            # 取当年表
                            tableyear = str(date.year)
                            queryset = getmodels("Entrydata", tableyear).objects
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
                                    (cond == "LMS" or cond == "LME") and int(date.month) < 2):
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
                                query_res = queryset.filter(**condtions).filter(target=membertarget).exclude(state="9")
                            if new_date:
                                query_res = queryset.filter(datadate__range=new_date).filter(
                                    target=membertarget).exclude(
                                    state="9")
                            if len(query_res) <= 0:
                                curvalue = 0
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
                                    else:
                                        value = query_res[0].curvalue
                                if col == 'm':
                                    if cond == "MAVG" or cond == "SAVG" or cond == "HAVG" or cond == "YAVG":
                                        value = query_res.aggregate(Avg('cumulativemonth'))["cumulativemonth__avg"]
                                    elif cond == "MMAX" or cond == "SMAX" or cond == "HMAX" or cond == "YMAX":
                                        value = query_res.aggregate(Max('cumulativemonth'))["cumulativemonth__max"]
                                    elif cond == "MMIN" or cond == "SMIN" or cond == "HMIN" or cond == "YMIN":
                                        value = query_res.aggregate(Min('cumulativemonth'))["cumulativemonth__min"]
                                    else:
                                        value = query_res[0].cumulativemonth
                                if col == 's':
                                    if cond == "MAVG" or cond == "SAVG" or cond == "HAVG" or cond == "YAVG":
                                        value = query_res.aggregate(Avg('cumulativequarter'))["cumulativequarter__avg"]
                                    elif cond == "MMAX" or cond == "SMAX" or cond == "HMAX" or cond == "YMAX":
                                        value = query_res.aggregate(Max('cumulativequarter'))["cumulativequarter__max"]
                                    elif cond == "MMIN" or cond == "SMIN" or cond == "HMIN" or cond == "YMIN":
                                        value = query_res.aggregate(Min('cumulativequarter'))["cumulativequarter__min"]
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
                                    else:
                                        value = query_res[0].cumulativehalfyear
                                if col == 'y':
                                    if cond == "MAVG" or cond == "SAVG" or cond == "HAVG" or cond == "YAVG":
                                        value = query_res.aggregate(Avg('cumulativeyear'))["cumulativeyear__avg"]
                                    elif cond == "MMAX" or cond == "SMAX" or cond == "HMAX" or cond == "YMAX":
                                        value = query_res.aggregate(Max('cumulativeyear'))["cumulativeyear__max"]
                                    elif cond == "MMIN" or cond == "SMIN" or cond == "HMIN" or cond == "YMIN":
                                        value = query_res.aggregate(Min('cumulativeyear'))["cumulativeyear__min"]
                                    else:
                                        value = query_res[0].cumulativeyear
                    # 公式中指标替换成值
                    formula = formula.replace("<" + th + ">", str(value))

        # 根据公式计算出值
        try:
            curvalue = eval(formula)
        except:
            pass

    calculatedata = tableList["Calculatedata"].objects.exclude(state="9").filter(target_id=target.id).filter(datadate=date)
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
    if target.cumulative == "是":
        cumulative = getcumulative(target, date, decimal.Decimal(str(calculatedata.curvalue)))
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
            "HMAX": "半年最大值", "HMIN": "半年最小值", "YMAX": "年最大值", "YMIN": "年最小值"
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

                                constant_chinese = '<' + constant_name + ':' + constant_col + '>(' + str(
                                    remove_decimal(value)) + ')'
                                formula_chinese = formula_chinese.replace(target_english, constant_chinese)

                            else:
                                target_name = target_codename[membertarget]
                                target_col = data_field[col]
                                target_cond = data_time[cond]

                                membertarget = Target.objects.filter(code=membertarget).exclude(state="9")

                                childid = None
                                if len(membertarget) <= 0:
                                    value = "指标不存在"
                                else:
                                    membertarget = membertarget[0]

                                    # 判断计算指标数据来源是否为外部系统

                                    tableyear = str(date.year)
                                    queryset = getmodels("Entrydata", tableyear).objects
                                    if cond == "LYS" or cond == "LYE" or (
                                            (cond == "LSS" or cond == "LSE") and int(date.month) < 4) or (
                                            (cond == "LHS" or cond == "LHE") and int(date.month) < 7) or (
                                            (cond == "LMS" or cond == "LME") and int(date.month) < 2):
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
                                            newdate = datetime.datetime(date.year + 1, 1, 1) + datetime.timedelta(days=-1)
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
                                            newdate = datetime.datetime(date.year + 1, 1, 1) + datetime.timedelta(days=-1)
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
                                        query_res = queryset.filter(**condtions).filter(target=membertarget).exclude(
                                            state="9").select_related("target")
                                    if new_date:
                                        query_res = queryset.filter(datadate__range=new_date).filter(
                                            target=membertarget).exclude(state="9")
                                    if len(query_res) <= 0:
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
                                            else:
                                                value = str(round(query_res[0].curvalue, query_res[0].target.digit))
                                                if operationtype == "17":
                                                    childid = str(query_res[0].id)
                                        if col == 'm':
                                            if cond == "MAVG" or cond == "SAVG" or cond == "HAVG" or cond == "YAVG":
                                                value = str(
                                                    round(
                                                        query_res.aggregate(Avg('cumulativemonth'))['cumulativemonth__avg'],
                                                        query_res[0].target.digit))
                                            elif cond == "MMAX" or cond == "SMAX" or cond == "HMAX" or cond == "YMAX":
                                                value = str(round(
                                                    query_res.aggregate(Max('cumulativemonth'))["cumulativemonth__max"],
                                                    query_res[0].target.digit))
                                            elif cond == "MMIN" or cond == "SMIN" or cond == "HMIN" or cond == "YMIN":
                                                value = str(round(
                                                    query_res.aggregate(Min('cumulativemonth'))["cumulativemonth__min"],
                                                    query_res[0].target.digit))
                                            else:
                                                value = str(round(query_res[0].cumulativemonth, query_res[0].target.digit))
                                        if col == 's':
                                            if cond == "MAVG" or cond == "SAVG" or cond == "HAVG" or cond == "YAVG":
                                                value = str(
                                                    round(
                                                        query_res.aggregate(Avg('cumulativequarter'))[
                                                            'cumulativequarter__avg'],
                                                        query_res[0].target.digit))
                                            elif cond == "MMAX" or cond == "SMAX" or cond == "HMAX" or cond == "YMAX":
                                                value = str(round(
                                                    query_res.aggregate(Max('cumulativequarter'))["cumulativequarter__max"],
                                                    query_res[0].target.digit))
                                            elif cond == "MMIN" or cond == "SMIN" or cond == "HMIN" or cond == "YMIN":
                                                value = str(round(
                                                    query_res.aggregate(Min('cumulativequarter'))["cumulativequarter__min"],
                                                    query_res[0].target.digit))
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
                                            else:
                                                value = str(
                                                    round(query_res[0].cumulativehalfyear, query_res[0].target.digit))
                                        if col == 'y':
                                            if cond == "MAVG" or cond == "SAVG" or cond == "HAVG" or cond == "YAVG":
                                                value = str(
                                                    round(query_res.aggregate(Avg('cumulativeyear'))['cumulativeyear__avg'],
                                                          query_res[0].target.digit))
                                            elif cond == "MMAX" or cond == "SMAX" or cond == "HMAX" or cond == "YMAX":
                                                value = str(
                                                    round(query_res.aggregate(Max('cumulativeyear'))["cumulativeyear__max"],
                                                          query_res[0].target.digit))
                                            elif cond == "MMIN" or cond == "SMIN" or cond == "HMIN" or cond == "YMIN":
                                                value = str(
                                                    round(query_res.aggregate(Min('cumulativeyear'))["cumulativeyear__min"],
                                                          query_res[0].target.digit))
                                            else:
                                                value = str(round(query_res[0].cumulativeyear, query_res[0].target.digit))

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
        all_constant = Constant.objects.exclude(state="9")
        all_target = Target.objects.exclude(state="9")
        tableyear = str(reporting_date.year)
        EntryTable = getmodels("Entrydata", tableyear)
        MeterTable = getmodels("Meterdata", tableyear)
        ExtractTable = getmodels("Extractdata", tableyear)
        CalculateTable = getmodels("Calculatedata", tableyear)
        tableList = {"Entrydata":EntryTable,"Meterdata":MeterTable,"Extractdata":ExtractTable,"Calculatedata":CalculateTable}


        for target in cur_target:
            if operationtype == "17":
                target = Target.objects.get(id=target.id)
                if target.calculateguid != str(guid):
                    try:
                        getcalculatedata(target, reporting_date, str(guid),all_constant,all_target,tableList)
                    except Exception as e:
                        print(e)
                        HttpResponse(0)
        return HttpResponse(1)


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
        for target in all_target:
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
                    if tablename != "":
                        cursor = connection.cursor()
                        strsql = "select  curvalue from " + tablename + " where target_id = " + str(
                            target.id) + " and datadate='" + reporting_date.strftime(
                            "%Y-%m-%d %H:%M:%S") + "'  order by id desc"
                        cursor.execute(strsql)
                        rows = cursor.fetchall()
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
                    if target.cumulative == "是":
                        cumulative = getcumulative(target, reporting_date, extractdata.curvalue)
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

        # 生成本次计算guid
        # 数据库中与本次guid不同的指标才参数计算
        guid = uuid.uuid1()
        cur_target = Target.objects.exclude(state="9").filter(adminapp_id=app, cycletype=cycletype,
                                                              operationtype=operationtype, work=work).order_by("sort")
        # 所有常数
        all_constant = Constant.objects.exclude(state="9")
        all_target = Target.objects.exclude(state="9")
        tableyear = str(reporting_date.year)

        EntryTable = getmodels("Entrydata", tableyear)
        MeterTable = getmodels("Meterdata", tableyear)
        ExtractTable = getmodels("Extractdata", tableyear)
        CalculateTable = getmodels("Calculatedata", tableyear)
        tableList = {"Entrydata":EntryTable,"Meterdata":MeterTable,"Extractdata":ExtractTable,"Calculatedata":CalculateTable}

        for target in cur_target:
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
                if tablename != "":
                    cursor = connection.cursor()
                    strsql = "select  curvalue from " + tablename + " where  target_id = " + str(
                        target.id) + " and  datadate='" + reporting_date.strftime(
                        "%Y-%m-%d %H:%M:%S") + "'  order by id desc"
                    cursor.execute(strsql)
                    rows = cursor.fetchall()
                    if len(rows) > 0:
                        try:
                            meterdata.twentyfourdata = rows[0][0]
                        except:
                            pass

                meterdata.target = target
                meterdata.datadate = reporting_date
                meterdata.metervalue = float(meterdata.twentyfourdata) - float(meterdata.zerodata)
                meterdata.curvalue = decimal.Decimal(float(meterdata.metervalue) * float(target.magnification))
                meterdata.curvalue = round(meterdata.curvalue, target.digit)
                if target.cumulative == "是":
                    cumulative = getcumulative(target, reporting_date, meterdata.curvalue)
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
                entrydata.curvalue = round(entrydata.curvalue, target.digit)
                if target.cumulative == "是":
                    cumulative = getcumulative(target, reporting_date, entrydata.curvalue)
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
                if tablename != "":
                    cursor = connection.cursor()
                    strsql = "select  curvalue from " + tablename + " where target_id = " + str(
                        target.id) + " and datadate='" + reporting_date.strftime(
                        "%Y-%m-%d %H:%M:%S") + "' order by id desc"
                    cursor.execute(strsql)
                    rows = cursor.fetchall()
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
                if target.cumulative == "是":
                    cumulative = getcumulative(target, reporting_date, extractdata.curvalue)
                    extractdata.cumulativemonth = cumulative["cumulativemonth"]
                    extractdata.cumulativequarter = cumulative["cumulativequarter"]
                    extractdata.cumulativehalfyear = cumulative["cumulativehalfyear"]
                    extractdata.cumulativeyear = cumulative["cumulativeyear"]
                extractdata.save()
            # 计算
            if operationtype == "17":
                target = Target.objects.get(id=target.id)
                # 为减少重复计算，判断指标calculate，如果指标calculate等于本次计算guid，则说明该指标在本次计算中以计算过
                if target.calculateguid != str(guid):
                    try:
                        getcalculatedata(target, reporting_date, str(guid),all_constant,all_target,tableList)
                    except Exception as e:
                        print(e)
                        HttpResponse(0)
        return HttpResponse(1)


def reporting_del(request):
    if request.user.is_authenticated():
        app = request.POST.get('app', '')
        cycletype = request.POST.get('cycletype', '')
        reporting_date = request.POST.get('reporting_date', '')
        operationtype = request.POST.get('operationtype', '')
        funid = request.POST.get('funid', '')
        work = None
        work_id = ""
        try:
            funid = int(funid)
            fun = Fun.objects.get(id=funid)
            work = fun.work
            work_id = fun.work_id
        except:
            pass
        try:
            app = int(app)
            reporting_date = getreporting_date(reporting_date, cycletype)
        except:
            return HttpResponse(0)

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
        for data in all_data:
            data.state = "9"
            data.releasestate = "0"
            data.save()

        username = UserInfo.objects.get(fullname=request.user.userinfo.fullname)
        user = username.user.id
        user_id = ""
        try:
            user_id = int(user)
        except:
            pass

        all_reportinglog = ReportingLog.objects.exclude(state="9").filter(datadate=reporting_date, work=work,
                                                                          cycletype=cycletype, adminapp_id=app,
                                                                          user_id=user_id)
        if len(all_reportinglog) > 0:
            all_reportinglog = all_reportinglog[0]
        else:
            all_reportinglog = ReportingLog()

        all_reportinglog.datadate = reporting_date
        all_reportinglog.cycletype = cycletype
        all_reportinglog.adminapp_id = app
        all_reportinglog.work_id = work_id
        all_reportinglog.user_id = user_id
        all_reportinglog.type = 'del'
        all_reportinglog.save()

        return HttpResponse(1)


def reporting_release(request):
    if request.user.is_authenticated():
        result = {}
        app = request.POST.get('app', '')
        savedata = request.POST.get('savedata')
        savedata = json.loads(savedata)
        cycletype = request.POST.get('cycletype', '')
        reporting_date = request.POST.get('reporting_date', '')
        funid = request.POST.get('funid', '')
        work = None
        work_id = ""
        try:
            funid = int(funid)
            fun = Fun.objects.get(id=funid)
            work = fun.work
            work_id = fun.work_id
        except:
            pass
        try:
            app = int(app)
            reporting_date = getreporting_date(reporting_date, cycletype)
        except:
            return HttpResponse(0)
        # 分别存入数据库
        savedata1 = savedata['1']
        savedata15 = savedata['15']
        savedata16 = savedata['16']
        savedata17 = savedata['17']

        def savedataall(savedata):
            if savedata.target.datatype == 'numbervalue':
                try:
                    savedata.curvalue = float(curdata["curvalue"])
                    savedata.curvalue = decimal.Decimal(str(savedata.curvalue)).quantize(
                        decimal.Decimal(Digit(savedata.target.digit)), rounding=decimal.ROUND_HALF_UP)
                except:
                    pass
            if savedata.target.datatype == 'date':
                try:
                    savedata.curvaluedate = datetime.datetime.strptime(curdata["curvaluedate"], "%Y-%m-%d %H:%M:%S")
                except:
                    pass
            if savedata.target.datatype == 'text':
                try:
                    savedata.curvaluetext = curdata["curvaluetext"]
                except:
                    pass
            try:
                savedata.zerodata = curdata["zerodata"]
            except:
                pass
            try:
                savedata.twentyfourdata = curdata["twentyfourdata"]
            except:
                pass
            try:
                savedata.metervalue = curdata["metervalue"]
            except:
                pass
            try:
                savedata.cumulativemonth = float(curdata["cumulativemonth"])
                savedata.cumulativemonth = round(savedata.cumulativemonth, savedata.target.digit)
            except:
                pass
            try:
                savedata.cumulativequarter = float(curdata["cumulativequarter"])
                savedata.cumulativequarter = round(savedata.cumulativequarter, savedata.target.digit)
            except:
                pass
            try:
                savedata.cumulativehalfyear = float(curdata["cumulativehalfyear"])
                savedata.cumulativehalfyear = round(savedata.cumulativehalfyear, savedata.target.digit)
            except:
                pass
            try:
                savedata.cumulativeyear = float(curdata["cumulativeyear"])
                savedata.cumulativeyear = round(savedata.cumulativeyear, savedata.target.digit)
            except:
                pass

            savedata.releasestate = '1'
            savedata.save()

        for curdata in savedata1:
            savedata = getmodels("Meterdata", str(reporting_date.year)).objects.exclude(state="9").get(
                id=int(curdata["id"]))
            if curdata["finalvalue"]:
                try:
                    newmagnification = float(curdata["magnification"])
                    if savedata.target.magnification != newmagnification:
                        savedata.target.magnification = newmagnification
                        savedata.target.save()
                except:
                    pass
                meterchangedata = Meterchangedata.objects.exclude(state="9").filter(meterdata=savedata.id)
                if len(meterchangedata) > 0:
                    meterchangedata = meterchangedata[0]
                else:
                    meterchangedata = Meterchangedata()

                reporting_date = datetime.datetime.strptime(curdata["reporting_date"], "%Y-%m-%d")
                try:
                    meterchangedata.datadate = reporting_date
                except:
                    pass
                try:
                    meterchangedata.meterdata = savedata.id
                except:
                    pass
                try:
                    meterchangedata.oldtable_zerodata = float(curdata["oldtable_zerodata"])
                except:
                    pass
                try:
                    meterchangedata.oldtable_twentyfourdata = float(curdata["oldtable_twentyfourdata"])
                except:
                    pass
                try:
                    meterchangedata.oldtable_value = float(curdata["oldtable_value"])
                except:
                    pass
                try:
                    meterchangedata.oldtable_magnification = float(curdata["oldtable_magnification"])
                except:
                    pass
                try:
                    meterchangedata.oldtable_finalvalue = float(curdata["oldtable_finalvalue"])
                except:
                    pass
                try:
                    meterchangedata.newtable_zerodata = float(curdata["newtable_zerodata"])
                except:
                    pass
                try:
                    meterchangedata.newtable_twentyfourdata = float(curdata["newtable_twentyfourdata"])
                except:
                    pass
                try:
                    meterchangedata.newtable_value = float(curdata["newtable_value"])
                except:
                    pass
                try:
                    meterchangedata.newtable_magnification = float(curdata["newtable_magnification"])
                except:
                    pass
                try:
                    meterchangedata.newtable_finalvalue = float(curdata["newtable_finalvalue"])
                except:
                    pass
                try:
                    meterchangedata.finalvalue = float(curdata["finalvalue"])
                except:
                    pass
                meterchangedata.save()

            savedataall(savedata)
        for curdata in savedata15:
            savedata = getmodels("Entrydata", str(reporting_date.year)).objects.exclude(state="9").get(
                id=int(curdata["id"]))
            savedataall(savedata)

        for curdata in savedata16:
            savedata = getmodels("Extractdata", str(reporting_date.year)).objects.exclude(state="9").get(
                id=int(curdata["id"]))
            savedataall(savedata)

        for curdata in savedata17:
            savedata = getmodels("Calculatedata", str(reporting_date.year)).objects.exclude(state="9").get(
                id=int(curdata["id"]))
            savedataall(savedata)

        username = UserInfo.objects.get(fullname=request.user.userinfo.fullname)
        user = username.user.id
        user_id = ""
        try:
            user_id = int(user)
        except:
            pass

        all_reportinglog = ReportingLog.objects.exclude(state="9").filter(datadate=reporting_date, work=work,
                                                                          cycletype=cycletype, adminapp_id=app,
                                                                          user_id=user_id)
        if len(all_reportinglog) > 0:
            all_reportinglog = all_reportinglog[0]
        else:
            all_reportinglog = ReportingLog()

        all_reportinglog.datadate = reporting_date
        all_reportinglog.cycletype = cycletype
        all_reportinglog.adminapp_id = app
        all_reportinglog.work_id = work_id
        all_reportinglog.user_id = user_id
        all_reportinglog.type = 'release'
        all_reportinglog.save()

    return HttpResponse(1)


def reporting_save(request):
    if request.user.is_authenticated():
        result = {}
        savedata = request.POST.get('savedata')
        operationtype = request.POST.get('operationtype')
        cycletype = request.POST.get('cycletype', '')
        savedata = json.loads(savedata)
        reporting_date = request.POST.get('reporting_date', '')
        try:
            reporting_date = getreporting_date(reporting_date, cycletype)
        except:
            return HttpResponse(0)
        for curdata in savedata:
            if operationtype == "1":
                savedata = getmodels("Meterdata", str(reporting_date.year)).objects.exclude(state="9").get(
                    id=int(curdata["id"]))
                if curdata["finalvalue"]:
                    try:
                        newmagnification = float(curdata["magnification"])
                        if savedata.target.magnification != newmagnification:
                            savedata.target.magnification = newmagnification
                            savedata.target.save()
                    except:
                        pass
                    meterchangedata = Meterchangedata.objects.exclude(state="9").filter(meterdata=savedata.id)
                    if len(meterchangedata) > 0:
                        meterchangedata = meterchangedata[0]
                    else:
                        meterchangedata = Meterchangedata()

                    reporting_date = datetime.datetime.strptime(curdata["reporting_date"], "%Y-%m-%d")
                    try:
                        meterchangedata.datadate = reporting_date
                    except:
                        pass
                    try:
                        meterchangedata.meterdata = savedata.id
                    except:
                        pass
                    try:
                        meterchangedata.oldtable_zerodata = float(curdata["oldtable_zerodata"])
                    except:
                        pass
                    try:
                        meterchangedata.oldtable_twentyfourdata = float(curdata["oldtable_twentyfourdata"])
                    except:
                        pass
                    try:
                        meterchangedata.oldtable_value = float(curdata["oldtable_value"])
                    except:
                        pass
                    try:
                        meterchangedata.oldtable_magnification = float(curdata["oldtable_magnification"])
                    except:
                        pass
                    try:
                        meterchangedata.oldtable_finalvalue = float(curdata["oldtable_finalvalue"])
                    except:
                        pass
                    try:
                        meterchangedata.newtable_zerodata = float(curdata["newtable_zerodata"])
                    except:
                        pass
                    try:
                        meterchangedata.newtable_twentyfourdata = float(curdata["newtable_twentyfourdata"])
                    except:
                        pass
                    try:
                        meterchangedata.newtable_value = float(curdata["newtable_value"])
                    except:
                        pass
                    try:
                        meterchangedata.newtable_magnification = float(curdata["newtable_magnification"])
                    except:
                        pass
                    try:
                        meterchangedata.newtable_finalvalue = float(curdata["newtable_finalvalue"])
                    except:
                        pass
                    try:
                        meterchangedata.finalvalue = float(curdata["finalvalue"])
                    except:
                        pass
                    meterchangedata.save()

            if operationtype == "15":
                savedata = getmodels("Entrydata", str(reporting_date.year)).objects.exclude(state="9").get(
                    id=int(curdata["id"]))
            if operationtype == "16":
                savedata = getmodels("Extractdata", str(reporting_date.year)).objects.exclude(state="9").get(
                    id=int(curdata["id"]))
            if operationtype == "17":
                savedata = getmodels("Calculatedata", str(reporting_date.year)).objects.exclude(state="9").get(
                    id=int(curdata["id"]))

            if savedata.target.datatype == 'numbervalue':
                try:
                    savedata.curvalue = float(curdata["curvalue"])
                    savedata.curvalue = decimal.Decimal(str(savedata.curvalue)).quantize(
                        decimal.Decimal(Digit(savedata.target.digit)),
                        rounding=decimal.ROUND_HALF_UP)
                except:
                    pass
            if savedata.target.datatype == 'date':
                try:
                    savedata.curvaluedate = datetime.datetime.strptime(curdata["curvaluedate"], "%Y-%m-%d %H:%M:%S")
                except:
                    pass
            if savedata.target.datatype == 'text':
                try:
                    savedata.curvaluetext = curdata["curvaluetext"]
                except:
                    pass
            try:
                savedata.zerodata = curdata["zerodata"]
            except:
                pass
            try:
                savedata.twentyfourdata = curdata["twentyfourdata"]
            except:
                pass
            try:
                savedata.metervalue = curdata["metervalue"]
            except:
                pass
            try:
                savedata.cumulativemonth = float(curdata["cumulativemonth"])
                savedata.cumulativemonth = round(savedata.cumulativemonth, savedata.target.digit)
            except:
                pass
            try:
                savedata.cumulativequarter = float(curdata["cumulativequarter"])
                savedata.cumulativequarter = round(savedata.cumulativequarter, savedata.target.digit)
            except:
                pass
            try:
                savedata.cumulativehalfyear = float(curdata["cumulativehalfyear"])
                savedata.cumulativehalfyear = round(savedata.cumulativehalfyear, savedata.target.digit)
            except:
                pass
            try:
                savedata.cumulativeyear = float(curdata["cumulativeyear"])
                savedata.cumulativeyear = round(savedata.cumulativeyear, savedata.target.digit)
            except:
                pass

            savedata.save()

    return HttpResponse(1)


def report_submit_index(request, funid):
    """
    报表上报
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
            elif search_report_type == "24":
                search_date = search_date
            elif search_report_type == "25":
                search_date = search_date
            elif search_report_type == "26":
                search_date = datetime.datetime.strptime(
                    datetime.datetime.strptime(search_date, "%Y").strftime("%Y-%m-%d"), "%Y-%m-%d")
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
            elif length_tag == 1:
                report_time = datetime.datetime.strptime(report_time, "%Y-%m") if report_time else None
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
            elif length_tag == 1:
                report_time = datetime.datetime.strptime(report_time, "%Y-%m") if report_time else None
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
                mychildfun.append(
                    {"id": fun.id, "name": fun.name, "url": url, "icon": fun.icon, "isselected": isselected,
                     "child": []})
            else:
                returnfuns = childfun(fun, funid)
                mychildfun.append({"id": fun.id, "name": fun.name, "url": url, "icon": fun.icon,
                                   "isselected": returnfuns["isselected"], "child": returnfuns["fun"]})
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
            # if len(fun.app.all()) > 0:
            if fun.app:
                url = fun.url + str(fun.id) + "/" if fun.url else ""
            if str(fun.id) == funid:
                isselected = True
                pagefuns.append(
                    {"id": fun.id, "name": fun.name, "url": url, "icon": fun.icon, "isselected": isselected,
                     "child": []})
            else:
                returnfuns = childfun(fun, funid)
                pagefuns.append({"id": fun.id, "name": fun.name, "url": url, "icon": fun.icon,
                                 "isselected": returnfuns["isselected"], "child": returnfuns["fun"]})
    curfun = Fun.objects.filter(id=int(funid))
    if len(curfun) > 0:
        myurl = curfun[0].url
        jsurl = curfun[0].url  # /falconstorswitch/24
        if myurl:
            myurl = myurl[:-1]
            jsurl = jsurl[1:-1]
            curjsurl = jsurl.split('/')
            jsurl = '/' + curjsurl[0]
            #
            # if "falconstorswitch" in myurl:
            #     compile_obj = re.compile(r"/.*/")
            #     jsurl = compile_obj.findall(myurl)[0][:-1]
        mycurfun = {
            "id": curfun[0].id, "name": curfun[0].name, "url": myurl, "jsurl": jsurl}
    return {"pagefuns": pagefuns, "curfun": mycurfun, "task_nums": task_nums}


def test(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        errors = []
        return render(request, 'test.html',
                      {'username': request.user.userinfo.fullname, "errors": errors})
    else:
        return HttpResponseRedirect("/login")


def index(request, funid):
    if request.user.is_authenticated():
        global funlist
        funlist = []
        if request.user.is_superuser == 1:
            allfunlist = Fun.objects.all()
            for fun in allfunlist:
                funlist.append(fun)
        else:
            cursor = connection.cursor()
            cursor.execute(
                "select datacenter_fun.id from datacenter_group,datacenter_fun,datacenter_userinfo,datacenter_userinfo_group,datacenter_group_fun "
                "where datacenter_group.id=datacenter_userinfo_group.group_id and datacenter_group.id=datacenter_group_fun.group_id and "
                "datacenter_group_fun.fun_id=datacenter_fun.id and datacenter_userinfo.id=datacenter_userinfo_group.userinfo_id and userinfo_id= "
                + str(request.user.userinfo.id) + " order by datacenter_fun.sort"
            )

            rows = cursor.fetchall()
            for row in rows:
                try:
                    fun = Fun.objects.get(id=row[0])
                    funlist = getfun(funlist, fun)
                except:
                    pass
        for index, value in enumerate(funlist):
            if value.sort is None:
                value.sort = 0
        funlist = sorted(funlist, key=lambda fun: fun.sort)

        # 右上角消息任务
        return render(request, "index.html",
                      {'username': request.user.userinfo.fullname, "homepage": True,
                       "pagefuns": getpagefuns(funid, request),
                       })
    else:
        return HttpResponseRedirect("/login")


def login(request):
    auth.logout(request)
    try:
        del request.session['ispuser']
        del request.session['isadmin']
    except KeyError:
        pass
    return render(request, 'login.html')


def userlogin(request):
    if request.method == 'POST':
        result = ""
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
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
                myuser = User.objects.get(username=username)
                usertype = myuser.userinfo.usertype
                if usertype == '1':
                    request.session['ispuser'] = True
                else:
                    request.session['ispuser'] = False
                request.session['isadmin'] = myuser.is_superuser
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


def get_fun_tree(parent, selectid, all_app):
    nodes = []
    children = parent.children.order_by("sort").exclude(state="9")
    for child in children:
        node = {}
        node["text"] = child.name
        node["id"] = child.id
        node["type"] = child.funtype
        # app应用
        # 当前节点的所有外键
        current_app = child.app
        if current_app:
            current_app_id = current_app.id
        else:
            current_app_id = ""

        app_select_list = []
        app_select_list.append({
            "app_name": "",
            "id": "",
            "app_state": "",
        })
        for app in all_app:
            works = app.work_set.exclude(state='9').values('id', 'name')
            app_select_list.append({
                "app_name": app.name,
                "id": app.id,
                "app_state": "selected" if app.id == current_app_id else "",
                "works": str(works),
            })

        selected_work = child.work_id

        node["data"] = {"url": child.url,
                        "icon": child.icon,
                        "pname": parent.name,
                        "app_list": app_select_list,
                        "app_div_show": True if child.funtype == "fun" else False,
                        "selected_work": selected_work
                        }
        node["children"] = get_fun_tree(child, selectid, all_app)

        try:
            if int(selectid) == child.id:
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
            all_app = App.objects.exclude(state="9")

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
                                funsave.save()

                                title = name
                        # 保存成功后，重新刷新页面，重新构造app_select_list
                        for c_app in all_app:
                            works_list = c_app.work_set.exclude(state='9').values('id', 'name')
                            pre_app_select_list.append({
                                "app_name": c_app.name,
                                "id": c_app.id,
                                "app_state": "selected" if str(c_app.id) == app else "",
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
                        else:
                            app_hidden_div = ""
                    except Exception as e:
                        print(e)
                        errors.append('保存失败。')
            treedata = []
            rootnodes = Fun.objects.order_by("sort").filter(pnode=None)
            if len(rootnodes) > 0:
                for rootnode in rootnodes:
                    root = {}
                    root["text"] = rootnode.name
                    root["id"] = rootnode.id
                    root["type"] = "node"

                    # 当前节点的所有外键
                    current_app = rootnode.app
                    if current_app:
                        current_app_id = current_app.id
                    else:
                        current_app_id = ""
                    app_select_list = []
                    app_select_list.append({
                        "app_name": "",
                        "id": "",
                        "app_state": "",
                    })
                    for app in all_app:
                        works = app.work_set.exclude(state='9').values('id', 'name')
                        app_select_list.append({
                            "app_name": app.name,
                            "id": app.id,
                            "app_state": "selected" if app.id == current_app_id else "",
                            "works": str(works),
                        })

                    selected_work = rootnode.work_id

                    root["data"] = {"url": rootnode.url,
                                    "icon": rootnode.icon,
                                    "pname": "无",
                                    "app_list": app_select_list,
                                    "app_div_show": True if rootnode.funtype == "fun" else False,
                                    "selected_work": selected_work,
                                    }
                    try:
                        if int(selectid) == rootnode.id:
                            root["state"] = {"opened": True, "selected": True}
                        else:
                            root["state"] = {"opened": True}
                    except:
                        root["state"] = {"opened": True}
                    root["children"] = get_fun_tree(rootnode, selectid, all_app)
                    treedata.append(root)

            treedata = json.dumps(treedata)
            return render(request, 'function.html',
                          {'username': request.user.userinfo.fullname, 'errors': errors, "id": id,
                           "pid": pid, "pname": pname, "name": name, "url": url, "icon": icon, "title": title,
                           "mytype": mytype, "hiddendiv": hiddendiv, "treedata": treedata,
                           "works_select_list": works_select_list,
                           "app_select_list": pre_app_select_list, "app_hidden_div": app_hidden_div,
                           "pagefuns": getpagefuns(funid, request=request)})
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
