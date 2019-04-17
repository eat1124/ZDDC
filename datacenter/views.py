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

from django.utils.timezone import utc
from django.utils.timezone import localtime
from django.shortcuts import render
from django.contrib import auth
from django.template import RequestContext
from django.http import HttpResponseRedirect, Http404, HttpResponse, JsonResponse, FileResponse
from django.http import StreamingHttpResponse
from django.db.models import Q
from django.db.models import Count
from django.db.models import Sum, Max
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from django.utils.encoding import escape_uri_path
from django.core.mail import send_mail
from django.forms.models import model_to_dict
from django.template.response import TemplateResponse
import calendar

from datacenter.tasks import *
from .models import *
from .remote import ServerByPara
from ZDDC import settings
from .funcs import *

funlist = []

info = {"webaddr": "cv-server", "port": "81", "username": "admin", "passwd": "Admin@2017", "token": "",
        "lastlogin": 0}


def process_monitor_index(request, funid):
    """
    进程监控
    """
    if request.user.is_authenticated():
        return render(request, 'process_monitor.html',
                      {'username': request.user.userinfo.fullname,
                       "pagefuns": getpagefuns(funid)})
    else:
        return HttpResponseRedirect("/login")


def process_monitor_data(request):
    if request.user.is_authenticated():
        result = []
        p_source = Source.objects.filter(pnode=None).exclude(state="9") 
        if p_source.exists():
            p_source = p_source[0]
        else:
            return JsonResponse({"data": []})
        all_source = Source.objects.exclude(state="9").filter(pnode=p_source)
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


def handle_process(source_id, handle_type=None):
    """
    开启程序
    """
    current_process = Source.objects.filter(id=source_id)
    tag = 0
    res = ""
    if current_process.exists():
        current_process = current_process[0]

        if handle_type == "RUN":
            try:
                process_path = BASE_DIR + os.sep + "utils" + os.sep + "handle_process.py" + " {0}".format(source_id)
                os.popen(r"{0}".format(process_path))
                res = "程序启动成功。"
                tag = 1
            except Exception as e:
                res = "程序启动失败"
            if tag == 1:
                # 修改数据库进程状态
                current_process.status = "running"
                current_process.create_time = datetime.datetime.now()
                current_process.save()
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
                            res = "程序终止成功。"
                            tag = 1
                        except:
                            res = "程序终止失败。"
                        break
                    else:
                        res = "未找到该进程"
            else:
                res = "该进程不存在。"
        else:
            res = "程序执行类型不符合。"
    else:
        res = "数据源不存在。"

    return (tag, res)


def process_run(request):
    if request.user.is_authenticated():
        source_id = request.POST.get("id", "")

        try:
            source_id = int(source_id)
        except:
            return JsonResponse({
                "res": "该数据源不存在。"
            })

        result = {}
        # 异步开启程序
        current_process = Source.objects.filter(id=source_id, status__in=["已关闭", "", "进程异常关闭，请重新启动。"]).exclude(
            state="9")
        if current_process.exists():
            tag, res = handle_process(source_id, handle_type="RUN")
            result["tag"] = tag
            result["res"] = res
        else:
            result["tag"] = 0
            result["res"] = "请勿重复执行该程序。"
        return JsonResponse(result)


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
                                        write_tag = True
                                        # 新增 或者 修改(且有my_file存在) 时写入文件
                                        if id == 0 or id != 0 and my_file:
                                            with open(myfilepath, 'wb+') as f:
                                                for chunk in my_file.chunks():
                                                    f.write(chunk)
                                            # 只要有文件写入，就发送请求
                                            # 远程执行命令，令远程windows发送请求下载文件
                                            local_script_dir = "C:\\Users\\Administrator\\Desktop\\test.ps1"
                                            remote_file_dir = "C:\\Users\\Administrator\\Desktop\\{0}".format(file_name)
                                            url_visited = "http://192.168.100.220:8000/download_file?file_name={0}".format(
                                                file_name)
                                            remote_cmd = r'powershell.exe -ExecutionPolicy RemoteSigned -file "{0}" "{1}" "{2}"'.format(
                                                local_script_dir, remote_file_dir, url_visited)
                                            remote_ip = "192.168.100.151"
                                            remote_user = "Administrator"
                                            remote_password = "tesunet@2017"
                                            remote_platform = "Windows"
                                            server_obj = ServerByPara(remote_cmd, remote_ip, remote_user,
                                                                      remote_password, remote_platform)
                                            result = server_obj.run("")
                                            if result["exec_tag"] != 0:
                                                write_tag = False

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
                                            errors.append('远程文件下载失败。')
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
                                        write_tag = True
                                        # 新增 或者 修改(且有my_file存在) 时写入文件
                                        if id == 0 or id != 0 and my_file:
                                            with open(myfilepath, 'wb+') as f:
                                                for chunk in my_file.chunks():
                                                    f.write(chunk)
                                            # 只要有文件写入，就发送请求
                                            # 远程执行命令，令远程windows发送请求下载文件

                                            local_script_dir = "C:\\Users\\Administrator\\Desktop\\test.ps1"
                                            remote_file_dir = r"E:\FineReport_10.0\webapps\webroot\WEB-INF\reportlets\{0}".format(file_name)
                                            # remote_file_dir = "C:\\Users\\Administrator\\Desktop\\{0}".format(file_name)
                                            url_visited = "http://192.168.100.224:8000/download_file?file_name={0}".format(
                                                file_name)
                                            remote_cmd = r'powershell.exe -ExecutionPolicy RemoteSigned -file "{0}" "{1}" "{2}"'.format(
                                                local_script_dir, remote_file_dir, url_visited)
                                            remote_ip = "192.168.100.151"
                                            remote_user = "Administrator"
                                            remote_password = "tesunet@2017"
                                            remote_platform = "Windows"
                                            server_obj = ServerByPara(remote_cmd, remote_ip, remote_user,
                                                                      remote_password, remote_platform)
                                            result = server_obj.run("")
                                            if result["exec_tag"] != 0:
                                                write_tag = False

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
                                            errors.append('远程文件下载失败。')
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
                                app_save.sort = int(
                                    sort) if sort else None
                                app_save.save()
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
            result.append({
                "id": app.id,
                "name": app.name,
                "code": app.code,
                "remark": app.remark,
                "sort": app.sort,
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
        for storage in all_storage:
            storagetype = storage.storagetype
            try:
                storagetype_dict_list = DictList.objects.filter(id=int(storage.storagetype))
                if storagetype_dict_list.exists():
                    storagetype_dict_list = storagetype_dict_list[0]
                    storagetype = storagetype_dict_list.name
            except:
                pass
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
                "code": storage.code,
                "tablename": storage.tablename,
                "storagetype_num": storage.storagetype,
                "validtime_num": storage.validtime,
                "storagetype": storagetype,
                "validtime": validtime,
                "sort": storage.sort,
            })

        return JsonResponse({"data": result})


def storage_save(request):
    if request.user.is_authenticated():
        id = request.POST.get("id", "")
        storage_name = request.POST.get("storage_name", "")
        storage_code = request.POST.get("storage_code", "")
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
            if storage_code.strip() == '':
                result["res"] = '存储代码不能为空。'
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
                                    code=storage_code).exclude(state="9")
                                if (len(all_storage) > 0):
                                    result["res"] = '存储代码:' + \
                                                    storage_code + '已存在。'
                                else:
                                    storage_save = Storage()
                                    storage_save.name = storage_name
                                    storage_save.code = storage_code
                                    storage_save.tablename = table_name
                                    storage_save.storagetype = storage_type
                                    storage_save.validtime = valid_time
                                    storage_save.sort = sort
                                    storage_save.save()
                                    result["res"] = "保存成功。"
                                    result["data"] = storage_save.id
                            else:
                                all_storage = Storage.objects.filter(code=storage_code).exclude(
                                    id=id).exclude(state="9")
                                if (len(all_storage) > 0):
                                    result["res"] = '存储代码:' + \
                                                    storage_code + '已存在。'
                                else:
                                    try:
                                        storage_save = Storage.objects.get(
                                            id=id)
                                        storage_save.name = storage_name
                                        storage_save.code = storage_code
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
            result.append({
                "id": cycle.id,
                "name": cycle.name,
                "code": cycle.code,
                "minutes": cycle.minutes,
                "create_date": cycle.creatdate.strftime('%Y-%m-%d %H:%M:%S') if cycle.creatdate else "",
                "sort": cycle.sort,
            })

        return JsonResponse({"data": result})


def cycle_save(request):
    if request.user.is_authenticated():
        id = request.POST.get("id", "")
        cycle_name = request.POST.get("cycle_name", "")
        cycle_code = request.POST.get("cycle_code", "")
        minutes = request.POST.get("minutes", "")
        create_date = request.POST.get("create_date", "")
        sort = request.POST.get("sort", "")
        try:
            id = int(id)
        except:
            raise Http404()
        result = {}

        if cycle_name.strip() == '':
            result["res"] = '周期名称不能为空。'
        else:
            if cycle_code.strip() == '':
                result["res"] = '周期代码不能为空。'
            else:
                if minutes.strip() == '':
                    result["res"] = '分钟不能为空。'
                else:
                    if create_date.strip() == '':
                        result["res"] = '开始时间不能为空。'
                    else:
                        if id == 0:
                            all_cycle = Cycle.objects.filter(
                                code=cycle_code).exclude(state="9")
                            if (len(all_cycle) > 0):
                                result["res"] = '存储代码:' + cycle_code + '已存在。'
                            else:
                                cycle_save = Cycle()
                                cycle_save.name = cycle_name
                                cycle_save.code = cycle_code
                                cycle_save.minutes = minutes
                                cycle_save.creatdate = create_date
                                cycle_save.sort = int(sort) if sort else None
                                cycle_save.save()
                                result["res"] = "保存成功。"
                                result["data"] = cycle_save.id
                        else:
                            all_cycle = Cycle.objects.filter(code=cycle_code).exclude(
                                id=id).exclude(state="9")
                            if (len(all_cycle) > 0):
                                result["res"] = '存储代码:' + cycle_code + '已存在。'
                            else:
                                try:
                                    cycle_save = Cycle.objects.get(id=id)
                                    cycle_save.name = cycle_name
                                    cycle_save.code = cycle_code
                                    cycle_save.minutes = minutes
                                    cycle_save.creatdate = create_date
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
                                                Source.objects.exclude(state="9").filter(pnode_id=None).aggregate(
                                                    Max("sort"))[
                                                    "sort__max"]
                                        else:
                                            max_sort_from_pnode = \
                                                Source.objects.exclude(state="9").filter(pnode_id=pid).aggregate(
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
                "sort").filter(pnode=None).exclude(state="9")

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
                    sort__gt=sort).exclude(state="9")
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
                    sort=old_position).exclude(state="9")[0]
            cur_source_obj.sort = position
            cur_source_id = cur_source_obj.id
            cur_source_obj.save()
            # 同一pnode
            if parent == old_parent:
                # 向上拽
                source_under_pnode = Source.objects.filter(pnode_id=old_parent).exclude(state="9").filter(
                    sort__gte=position,
                    sort__lt=old_position).exclude(id=cur_source_id)
                for source in source_under_pnode:
                    source.sort += 1
                    source.save()

                # 向下拽
                source_under_pnode = Source.objects.filter(pnode_id=old_parent).exclude(state="9").filter(
                    sort__gt=old_position, sort__lte=position).exclude(id=cur_source_id)
                for source in source_under_pnode:
                    source.sort -= 1
                    source.save()

            # 向其他节点拽
            else:
                # 原来pnode下
                old_source = Source.objects.filter(pnode_id=old_parent).exclude(state="9").filter(
                    sort__gt=old_position).exclude(id=cur_source_id)
                for step in old_source:
                    step.sort -= 1
                    step.save()
                # 后来pnode下
                cur_source = Source.objects.filter(pnode_id=parent).exclude(state="9").filter(
                    sort__gte=position).exclude(
                    id=cur_source_id)
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
        sourcelist = Source.objects.all().exclude(state='9').exclude(pnode=None)
        for i in sourcelist:
            source_list.append({
                "source_name": i.name,
                "source_id": i.id,
            })
        print(len(sourcelist))

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

        all_target = Target.objects.exclude(state="9").order_by("sort")
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

        for target in all_target:
            operationtype = target.operationtype
            try:
                operationtype_dict_list = DictList.objects.filter(id=int(target.operationtype))
                if operationtype_dict_list.exists():
                    operationtype_dict_list = operationtype_dict_list[0]
                    operationtype = operationtype_dict_list.name
            except:
                pass

            cycletype = target.cycletype
            try:
                cycletype_dict_list = DictList.objects.filter(id=int(target.cycletype))
                if cycletype_dict_list.exists():
                    cycletype_dict_list = cycletype_dict_list[0]
                    cycletype = cycletype_dict_list.name
            except:
                pass

            businesstype = target.businesstype
            try:
                businesstype_dict_list = DictList.objects.filter(id=int(target.businesstype))
                if businesstype_dict_list.exists():
                    businesstype_dict_list = businesstype_dict_list[0]
                    businesstype = businesstype_dict_list.name
            except:
                pass

            unit = target.unit
            try:
                unit_dict_list = DictList.objects.filter(id=int(target.unit))
                if unit_dict_list.exists():
                    unit_dict_list = unit_dict_list[0]
                    unit = unit_dict_list.name
            except:
                pass

            applist = []
            for my_app in target.app.all():
                applist.append(my_app.id)

            adminapp_name = ""
            try:
                adminapp_name = target.adminapp.name
            except:
                pass

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
                "cumulative": target.cumulative,
                "upperlimit": target.upperlimit,
                "lowerlimit": target.lowerlimit,
                "formula": target.formula,
                "cycle": target.cycle_id,
                "source": target.source_id,
                "sourcetable": target.sourcetable,
                "sourcefields": target.sourcefields,
                "sourceconditions": target.sourceconditions,
                "sourcesis": target.sourcesis,
                "storage": target.storage_id,
                "storagefields": target.storagefields,
                "storagetag": target.storagetag,
                "sort": target.sort,
                "state": target.state,
                "remark": target.remark,
            })
        return JsonResponse({"data": result})


def target_save(request):
    if request.user.is_authenticated():
        id = request.POST.get("id", "")
        name = request.POST.get("name", "")
        code = request.POST.get("code", "")
        operationtype = request.POST.get("operationtype", "")
        cycletype = request.POST.get("cycletype", "")
        businesstype = request.POST.get("businesstype", "")
        unit = request.POST.get("unit", "")
        magnification = request.POST.get("magnification", "")
        digit = request.POST.get("digit", "")
        upperlimit = request.POST.get("upperlimit", "")
        lowerlimit = request.POST.get("lowerlimit", "")
        adminapp = request.POST.get("adminapp", "")
        app_list = request.POST.getlist('app[]')
        cumulative = request.POST.get("cumulative", "")
        sort = request.POST.get("sort", "")

        formula = request.POST.get("formula", "")

        cycle = request.POST.get("cycle", "")
        source = request.POST.get("source", "")
        sourcetable = request.POST.get("sourcetable", "")
        sourcesis = request.POST.get("sourcesis", "")
        sourcefields = request.POST.get("sourcefields", "")
        sourceconditions = request.POST.get("sourceconditions", "")
        storage = request.POST.get("storage", "")
        storagetag = request.POST.get("storagetag", "")
        storagefields = request.POST.get("storagefields", "")

        savetype = request.POST.get("savetype", "")

        all_app = App.objects.exclude(state="9")
        all_cycle = Cycle.objects.exclude(state="9")
        all_source = Source.objects.exclude(state="9")
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
                                if id == 0:
                                    all_target = Target.objects.filter(
                                        code=code).exclude(state="9")
                                    if (len(all_target) > 0):
                                        result["res"] = '指标代码:' + \
                                                        code + '已存在。'
                                    else:
                                        all_target = Target.objects.filter(
                                            name=name).exclude(state="9")
                                        if (len(all_target) > 0):
                                            result["res"] = '指标名称:' + \
                                                            code + '已存在。'
                                        else:
                                            target_save = Target()
                                            target_save.name = name
                                            target_save.code = code
                                            target_save.operationtype = operationtype
                                            target_save.cycletype = cycletype
                                            target_save.businesstype = businesstype
                                            target_save.unit = unit
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
                                            try:
                                                app_id = int(adminapp)
                                                my_app = all_app.get(id=app_id)
                                                target_save.adminapp = my_app
                                            except:
                                                pass
                                            target_save.cumulative = cumulative
                                            try:
                                                target_save.sort = int(sort)
                                            except:
                                                pass
                                            if operationtype == '17':
                                                target_save.formula = formula
                                            if operationtype == '16':
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
                                                target_save.sourcetable = sourcetable
                                                target_save.sourcesis = sourcesis
                                                target_save.sourcefields = sourcefields
                                                target_save.sourceconditions = sourceconditions
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
                                    all_target = Target.objects.filter(code=code).exclude(
                                        id=id).exclude(state="9")
                                    if (len(all_target) > 0):
                                        result["res"] = '指标代码:' + \
                                                        code + '已存在。'
                                    else:
                                        all_target = Target.objects.filter(name=name).exclude(
                                            id=id).exclude(state="9")
                                        if (len(all_target) > 0):
                                            result["res"] = '指标名称:' + \
                                                            code + '已存在。'
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
                                                try:
                                                    app_id = int(adminapp)
                                                    my_app = all_app.get(id=app_id)
                                                    target_save.adminapp = my_app
                                                except:
                                                    pass
                                                target_save.cumulative = cumulative
                                                try:
                                                    target_save.sort = int(sort)
                                                except:
                                                    pass
                                                if operationtype == '17':
                                                    target_save.formula = formula
                                                if operationtype == '16':
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
                                                    target_save.sourcetable = sourcetable
                                                    target_save.sourcesis = sourcesis
                                                    target_save.sourcefields = sourcefields
                                                    target_save.sourceconditions = sourceconditions
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

        sourcelist = Source.objects.all().exclude(state='9')
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
        return render(request, 'target_app.html',
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

        sourcelist = Source.objects.all().exclude(state='9')
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


def reporting_index(request, cycletype, funid):
    """
    数据填报
    """
    if request.user.is_authenticated():
        app = ""
        try:
            cur_fun = Fun.objects.filter(id=int(funid)).exclude(state='9')
            app = cur_fun[0].app_id
        except:
            return HttpResponseRedirect("/index")
        now = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=-1)
        date = now.strftime("%Y-%m-%d")
        if cycletype == '10':
            now = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(
                days=-1)
            date = now.strftime("%Y-%m-%d")
        if cycletype == '11':
            now = (datetime.datetime.now().replace(day=1, hour=0, minute=0, second=0,
                                                   microsecond=0) + datetime.timedelta(
                days=-1)).replace(day=1)
            date = now.strftime("%Y-%m")
        if cycletype == '12':
            now = (datetime.datetime.now().replace(day=1, hour=0, minute=0, second=0,
                                                   microsecond=0) + datetime.timedelta(
                days=-1)).replace(day=1)
            date = now.strftime("%Y-%m")
        if cycletype == '13':
            now = (datetime.datetime.now().replace(day=1, hour=0, minute=0, second=0,
                                                   microsecond=0) + datetime.timedelta(
                days=-1)).replace(day=1)
            date = now.strftime("%Y-%m")
        if cycletype == '14':
            now = (datetime.datetime.now().replace(month=1, day=1, hour=0, minute=0, second=0,
                                                   microsecond=0) + datetime.timedelta(
                days=-1)).replace(month=1, day=1)
            date = now.strftime("%Y")

        entrytag = ""
        extracttag = ""
        calculatetag = ""

        entrynew = ""
        extractnew = ""
        calculatenew = ""

        entryreset = ""
        extractreset = ""
        calculatereset = ""

        entry_target = Target.objects.exclude(state='9').filter(cycletype=cycletype, adminapp_id=app,
                                                                operationtype='15')
        extract_target = Target.objects.exclude(state='9').filter(cycletype=cycletype, adminapp_id=app,
                                                                  operationtype='16')
        calculate_target = Target.objects.exclude(state='9').filter(cycletype=cycletype, adminapp_id=app,
                                                                    operationtype='17')

        entry_data = Entrydata.objects.exclude(state="9").filter(target__adminapp_id=app, target__cycletype=cycletype,
                                                                 datadate=now)
        extract_data = Extractdata.objects.exclude(state="9").filter(target__adminapp_id=app,
                                                                     target__cycletype=cycletype, datadate=now)
        calculate_data = Calculatedata.objects.exclude(state="9").filter(target__adminapp_id=app,
                                                                         target__cycletype=cycletype, datadate=now)
        if len(entry_target) <= 0 and len(entry_data) <= 0:
            entrytag = "display: none;"
        if len(extract_target) <= 0 and len(extract_data) <= 0:
            extracttag = "display: none;"
        if len(calculate_target) <= 0 and len(calculate_data) <= 0:
            calculatetag = "display: none;"
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
                       "entrytag": entrytag,
                       "extracttag": extracttag,
                       "calculatetag": calculatetag,
                       "entrynew": entrynew,
                       "extractnew": extractnew,
                       "calculatenew": calculatenew,
                       "entryreset": entryreset,
                       "extractreset": extractreset,
                       "calculatereset": calculatereset,
                       "pagefuns": getpagefuns(funid)})
    else:
        return HttpResponseRedirect("/login")


def reporting_data(request):
    if request.user.is_authenticated():

        result = []
        app = request.GET.get('app', '')
        cycletype = request.GET.get('cycletype', '')
        reporting_date = request.GET.get('reporting_date', '')
        operationtype = request.GET.get('operationtype', '')
        try:
            app = int(app)
            if cycletype == "10":
                reporting_date = datetime.datetime.strptime(reporting_date, "%Y-%m-%d")
            if cycletype == "11":
                reporting_date = datetime.datetime.strptime(reporting_date, "%Y-%m")
            if cycletype == "12":
                reporting_date = datetime.datetime.strptime(reporting_date, "%Y-%m")
            if cycletype == "13":
                reporting_date = datetime.datetime.strptime(reporting_date, "%Y-%m")
            if cycletype == "14":
                reporting_date = datetime.datetime.strptime(reporting_date, "%Y")
        except:
            raise Http404()

        all_data = []
        if operationtype == "0":
            curapp = App.objects.get(id=app)
            all_data = Entrydata.objects.exclude(state="9").filter(target__app=curapp, target__cycletype=cycletype,
                                                                   datadate=reporting_date)
        if operationtype == "15":
            all_data = Entrydata.objects.exclude(state="9").filter(target__adminapp_id=app, target__cycletype=cycletype,
                                                                   datadate=reporting_date)
        if operationtype == "16":
            all_data = Extractdata.objects.exclude(state="9").filter(target__adminapp_id=app,
                                                                     target__cycletype=cycletype,
                                                                     datadate=reporting_date)
        if operationtype == "17":
            all_data = Calculatedata.objects.exclude(state="9").filter(target__adminapp_id=app,
                                                                       target__cycletype=cycletype,
                                                                       datadate=reporting_date)
        for data in all_data:
            businesstypename = data.target.businesstype
            unitname = data.target.unit
            try:
                businesstype_dict_list = DictList.objects.filter(id=int(data.target.businesstype))
                if businesstype_dict_list.exists():
                    businesstype_dict_list = businesstype_dict_list[0]
                    businesstypename = businesstype_dict_list.name
            except:
                pass
            try:
                unit_dict_list = DictList.objects.filter(id=int(data.target.unit))
                if unit_dict_list.exists():
                    unit_dict_list = unit_dict_list[0]
                    unitname = unit_dict_list.name
            except:
                pass
            cumulativemonth = ""
            cumulativequarter = ""
            cumulativehalfyear = ""
            cumulativeyear = ""
            if data.target.cumulative == '是':
                cumulativemonth = round(data.cumulativemonth, data.target.digit)
                cumulativequarter = round(data.cumulativequarter, data.target.digit)
                cumulativehalfyear = round(data.cumulativehalfyear, data.target.digit)
                cumulativeyear = round(data.cumulativeyear, data.target.digit)
            result.append({
                "id": data.id,
                "curvalue": round(data.curvalue, data.target.digit),
                "cumulativemonth": cumulativemonth,
                "cumulativequarter": cumulativequarter,
                "cumulativehalfyear": cumulativehalfyear,
                "cumulativeyear": cumulativeyear,
                "target_id": data.target.id,
                "target_name": data.target.name,
                "target_code": data.target.code,
                "target_businesstype": data.target.businesstype,
                "target_unit": data.target.unit,
                "target_businesstypename": businesstypename,
                "target_unitname": unitname,
                "target_cumulative": data.target.cumulative,
                "target_upperlimit": data.target.upperlimit,
                "target_lowerlimit": data.target.lowerlimit,
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

    all_data = []
    if target.operationtype == "15":
        all_data = Entrydata.objects.exclude(state="9").filter(target=target, datadate=lastg_date)
    if target.operationtype == "16":
        all_data = Extractdata.objects.exclude(state="9").filter(target=target, datadate=lastg_date)
    if target.operationtype == "17":
        all_data = Calculatedata.objects.exclude(state="9").filter(target=target, datadate=lastg_date)
    if len(all_data) > 0:
        cumulativemonth = all_data[0].cumulativemonth + value
        cumulativequarter = all_data[0].cumulativequarter + value
        cumulativehalfyear = all_data[0].cumulativehalfyear + value
        cumulativeyear = all_data[0].cumulativeyear + value
    return {"cumulativemonth": cumulativemonth, "cumulativequarter": cumulativequarter,
            "cumulativehalfyear": cumulativehalfyear, "cumulativeyear": cumulativeyear}


def getextractdata(target, date):
    """
    数据提取
    """
    curvalue = 0

    con = target.source.connection
    con = json.loads(con)
    db = pymysql.connect(con[0]["host"], con[0]["user"], con[0]["passwd"], con[0]["db"])
    cursor = db.cursor()
    strsql = "select " + target.sourcefields + " from " + target.sourcetable + " where " + target.sourceconditions
    cursor.execute(strsql)
    data = cursor.fetchall()
    if len(data) > 0:
        curvalue = data[0][0]
    db.close()
    print("Database version : %s " % curvalue)

    return curvalue


def getcalculatedata(target, date, guid):
    """
    数据计算
    """
    curvalue = 0
    formula = ""
    if target.formula is not None:
        formula = target.formula.replace(" ", "")
    members = formula.split('>')
    for member in members:
        if member.replace(" ", "") != "":
            col = "d";
            cond = "D";
            if (member.find('<') >= 0):
                membertarget = member[member.find('<') + 1:]
                th = membertarget
                if membertarget.find(':') > 0:
                    col = membertarget[membertarget.find(':') + 1:]
                    membertarget = membertarget[0:membertarget.find(':')]
                    if col.find(':') > 0:
                        cond = col[col.find(':') + 1:]
                        col = col[0:col.find(':')]
                membertarget = Target.objects.filter(code=membertarget).exclude(state="9")
                if len(membertarget) <= 0:
                    curvalue = 0
                else:
                    queryset = Entrydata.objects
                    membertarget = membertarget[0]
                    if membertarget.operationtype == target.operationtype and membertarget.adminapp_id == target.adminapp_id and membertarget.cycletype == target.cycletype and membertarget.calculateguid != guid:
                        getcalculatedata(membertarget, date, guid)
                    operationtype = membertarget.operationtype
                    if operationtype == "15":
                        queryset = Entrydata.objects
                    if operationtype == "16":
                        queryset = Extractdata.objects
                    if operationtype == "17":
                        queryset = Calculatedata.objects
                    condtions = {'datadate': date}
                    if cond == "D":
                        condtions = {'datadate': date}
                    if cond == "M":
                        condtions = {'datadate__year': date.year, 'datadate__month': date.month}
                    if cond == "Y":
                        condtions = {'datadate__year': date.year}
                    if cond == "ME":
                        year = date.year
                        month = date.month
                        a, b = calendar.monthrange(year, month)  # a,b——weekday的第一天是星期几（0-6对应星期一到星期天）和这个月的所有天数
                        date_now = datetime.datetime(year=year, month=month, day=b)  # 构造本月1号datetime
                        newdate = date_now + datetime.timedelta(days=1)  # 上月datetime
                        condtions = {'datadate': newdate}
                    if cond == "YE":
                        newdate = date.replace(month=12, day=31)
                        condtions = {'datadate': newdate}
                    if cond == "MS":
                        newdate = date.replace(day=1)
                        condtions = {'datadate': newdate}
                    if cond == "YS":
                        newdate = date.replace(month=1, day=1)
                        condtions = {'datadate': newdate}
                    query_res = queryset.filter(**condtions).filter(target=membertarget).exclude(state="9")
                    if len(query_res) <= 0:
                        curvalue = 0
                    else:
                        value = 0
                        if col == 'd':
                            value = query_res[0].curvalue
                        if col == 'm':
                            value = query_res[0].cumulativemonth
                        if col == 's':
                            value = query_res[0].cumulativequarter
                        if col == 'h':
                            value = query_res[0].cumulativehalfyear
                        if col == 'y':
                            value = query_res[0].cumulativeyear
                        formula = formula.replace("<" + th + ">", str(value));

    try:
        curvalue = eval(formula)
    except:
        pass
    calculatedata = Calculatedata()
    calculatedata.target = target
    calculatedata.datadate = date
    calculatedata.curvalue = curvalue
    if target.cumulative == "是":
        cumulative = getcumulative(target, date, decimal.Decimal(str(calculatedata.curvalue)))
        calculatedata.cumulativemonth = cumulative["cumulativemonth"]
        calculatedata.cumulativequarter = cumulative["cumulativequarter"]
        calculatedata.cumulativehalfyear = cumulative["cumulativehalfyear"]
        calculatedata.cumulativeyear = cumulative["cumulativeyear"]
    calculatedata.formula = target.formula
    calculatedata.save()
    target.calculateguid = guid
    target.save()


def reporting_new(request):
    if request.user.is_authenticated():
        app = request.POST.get('app', '')
        cycletype = request.POST.get('cycletype', '')
        reporting_date = request.POST.get('reporting_date', '')
        operationtype = request.POST.get('operationtype', '')
        try:
            app = int(app)
            if cycletype == "10":
                reporting_date = datetime.datetime.strptime(reporting_date, "%Y-%m-%d")
            if cycletype == "11":
                reporting_date = datetime.datetime.strptime(reporting_date, "%Y-%m")
            if cycletype == "12":
                reporting_date = datetime.datetime.strptime(reporting_date, "%Y-%m")
            if cycletype == "13":
                reporting_date = datetime.datetime.strptime(reporting_date, "%Y-%m")
            if cycletype == "14":
                reporting_date = datetime.datetime.strptime(reporting_date, "%Y")
        except:
            return HttpResponse(0)

        guid = uuid.uuid1()
        all_target = Target.objects.exclude(state="9").filter(adminapp_id=app, cycletype=cycletype,
                                                              operationtype=operationtype)
        for target in all_target:
            if operationtype == "15":
                entrydata = Entrydata()
                entrydata.target = target
                entrydata.datadate = reporting_date
                entrydata.curvalue = 0
                if target.cumulative == "是":
                    cumulative = getcumulative(target, reporting_date, entrydata.curvalue)
                    entrydata.cumulativemonth = cumulative["cumulativemonth"]
                    entrydata.cumulativequarter = cumulative["cumulativequarter"]
                    entrydata.cumulativehalfyear = cumulative["cumulativehalfyear"]
                    entrydata.cumulativeyear = cumulative["cumulativeyear"]
                entrydata.save()
            if operationtype == "16":
                extractdata = Extractdata.objects.filter(state="8", target=target, datadate=reporting_date)
                if len(extractdata) > 0:
                    extractdata = extractdata[0]
                    extractdata.state = ""
                    extractdata.save()
                else:
                    extractdata = Extractdata()
                    extractdata.target = target
                    extractdata.datadate = reporting_date
                    extractdata.curvalue = getextractdata(target, reporting_date)
                    if target.cumulative == "是":
                        cumulative = getcumulative(target, reporting_date, extractdata.curvalue)
                        extractdata.cumulativemonth = cumulative["cumulativemonth"]
                        extractdata.cumulativequarter = cumulative["cumulativequarter"]
                        extractdata.cumulativehalfyear = cumulative["cumulativehalfyear"]
                        extractdata.cumulativeyear = cumulative["cumulativeyear"]
                    extractdata.save()
            if operationtype == "17":
                target = Target.objects.get(id=target.id)
                if target.calculateguid != str(guid):
                    getcalculatedata(target, reporting_date, str(guid))
        return HttpResponse(1)


def reporting_del(request):
    if request.user.is_authenticated():
        app = request.POST.get('app', '')
        cycletype = request.POST.get('cycletype', '')
        reporting_date = request.POST.get('reporting_date', '')
        operationtype = request.POST.get('operationtype', '')
        try:
            app = int(app)
            if cycletype == "10":
                reporting_date = datetime.datetime.strptime(reporting_date, "%Y-%m-%d")
            if cycletype == "11":
                reporting_date = datetime.datetime.strptime(reporting_date, "%Y-%m")
            if cycletype == "12":
                reporting_date = datetime.datetime.strptime(reporting_date, "%Y-%m")
            if cycletype == "13":
                reporting_date = datetime.datetime.strptime(reporting_date, "%Y-%m")
            if cycletype == "14":
                reporting_date = datetime.datetime.strptime(reporting_date, "%Y")
        except:
            return HttpResponse(0)

        all_data = []
        if operationtype == "15":
            all_data = Entrydata.objects.exclude(state="9").filter(target__adminapp_id=app, target__cycletype=cycletype,
                                                                   datadate=reporting_date)
        if operationtype == "16":
            all_data = Extractdata.objects.exclude(state="9").filter(target__adminapp_id=app,
                                                                     target__cycletype=cycletype,
                                                                     datadate=reporting_date)
        if operationtype == "17":
            all_data = Calculatedata.objects.exclude(state="9").filter(target__adminapp_id=app,
                                                                       target__cycletype=cycletype,
                                                                       datadate=reporting_date)
        for data in all_data:
            data.state = "9"
            data.save()

        return HttpResponse(1)


def reporting_save(request):
    if request.user.is_authenticated():
        result = {}
        savedata = request.POST.get('savedata')
        operationtype = request.POST.get('operationtype')
        savedata = json.loads(savedata)
        for curdata in savedata:
            if operationtype == "15":
                savedata = Entrydata.objects.exclude(state="9").get(id=int(curdata["id"]))
            if operationtype == "16":
                savedata = Extractdata.objects.exclude(state="9").get(id=int(curdata["id"]))
            if operationtype == "17":
                savedata = Calculatedata.objects.exclude(state="9").get(id=int(curdata["id"]))
            try:
                savedata.curvalue = float(curdata["curvalue"])
            except:
                pass
            try:
                savedata.cumulativemonth = float(curdata["cumulativemonth"])
            except:
                pass

            try:
                savedata.cumulativequarter = float(curdata["cumulativequarter"])
            except:
                pass

            try:
                savedata.cumulativehalfyear = float(curdata["cumulativehalfyear"])
            except:
                pass

            try:
                savedata.cumulativeyear = float(curdata["cumulativeyear"])
            except:
                pass
            savedata.save()

        result["res"] = "保存成功。"

    return JsonResponse(result)


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
        date3 = (datetime.datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(
            days=-1)).replace(day=1)
        date4 = (datetime.datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(
            days=-1)).replace(day=1)
        date5 = (datetime.datetime.now().replace(month=1, day=1, hour=0, minute=0, second=0,
                                                 microsecond=0) + datetime.timedelta(
            days=-1)).replace(month=1, day=1)

        temp_dict = {
            "22": date1.strftime("%Y-%m-%d"),
            "23": date2.strftime("%Y-%m"),
            "24": date3.strftime("%Y-%m"),
            "25": date4.strftime("%Y-%m"),
            "26": date5.strftime("%Y"),
        }

        return render(request, 'report_submit.html',
                      {'username': request.user.userinfo.fullname,
                       "report_type_list": report_type_list,
                       "all_app_list": all_app_list,
                       "errors": errors,
                       "id": id,
                       "date": json.dumps(temp_dict),
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
        state_dict = {
            "0": "未发布",
            "1": "已发布",
            "": "未创建",
        }
        # 时间的过滤
        if search_date:
            if search_report_type == "22":
                search_date = datetime.datetime.strptime(search_date, "%Y-%m-%d")
            elif search_report_type in ["23", "24", "25"]:
                search_date = datetime.datetime.strptime(search_date, "%Y-%m")
            elif search_report_type == "26":
                search_date = datetime.datetime.strptime(
                    datetime.datetime.strptime(search_date, "%Y").strftime("%Y-%m-%d"), "%Y-%m-%d")
        else:
            pass

        all_report = ReportModel.objects.exclude(state="9").order_by("sort").filter(report_type=search_report_type)
        curadminapp = App.objects.get(id=int(search_app))
        all_report = all_report.filter(app=curadminapp)

        for report in all_report:
            # report_submit
            report_submit = report.reportsubmit_set.exclude(state="9")
            if report_submit.exists():
                report_submit = report_submit[0]
            else:
                report_submit = ""

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

            report_time = ""
            # 区分是否保存/发布
            if report_submit:
                if search_date:
                    current_report_submit = report.reportsubmit_set.exclude(state="9").filter(report_time=search_date)
                else:
                    current_report_submit = report.reportsubmit_set.exclude(state="9")
                if current_report_submit.exists():
                    current_report_submit = current_report_submit[0]

                    # 存在report_time
                    report_time = current_report_submit.report_time
                    if report.report_type == "22":
                        report_time = report_time.strftime("%Y-%m-%d")
                    elif report.report_type in ["23", "24", "25"]:
                        report_time = report_time.strftime("%Y-%m")
                    elif report.report_type == "26":
                        report_time = report_time.strftime("%Y")

                    current_report_submit_info_set = current_report_submit.reportsubmitinfo_set.exclude(state="9")
                    if current_report_submit_info_set.exists():
                        for report_submit_info in current_report_submit_info_set:
                            report_info_list.append({
                                "report_info_name": report_submit_info.name,
                                "report_info_value": report_submit_info.value,
                                "report_info_id": int(report_submit_info.id),
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
                        "person": report_submit.person if report_submit else str(request.user),
                        "write_time": report_submit.write_time.strftime(
                            '%Y-%m-%d') if report_submit else datetime.datetime.now().strftime('%Y-%m-%d'),
                        "state": report_submit.state if report_submit else "",
                        "state_desc": state_dict[report_submit.state] if report_submit else state_dict[""],
                        "report_time": report_time,
                    })
            else:
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
                    "person": report_submit.person if report_submit else str(request.user),
                    "write_time": report_submit.write_time.strftime(
                        '%Y-%m-%d') if report_submit else datetime.datetime.now().strftime('%Y-%m-%d'),
                    "state": report_submit.state if report_submit else "",
                    "state_desc": state_dict[report_submit.state] if report_submit else state_dict[""],
                    "report_time": report_time,
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

                current_report_submit = ReportSubmit.objects.exclude(state="9").filter(report_model_id=report_model)
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
            try:
                id = int(id)
            except:
                raise Http404()
            report = ReportModel.objects.filter(id=id)

            if report.exists():
                report = report[0]
                # 删除关联report_submit
                report_submit_set = report.reportsubmit_set.exclude(state="9")
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


def processindex(request, processrun_id):
    if request.user.is_authenticated():
        errors = []
        # processrun_id = request.GET.get("p_run_id", "")
        s_tag = request.GET.get("s", "")
        c_process_run = ProcessRun.objects.filter(
            id=processrun_id).select_related("process")
        if c_process_run.exists():
            process_url = c_process_run[0].process.url
            process_name = c_process_run[0].process.name
            process_id = c_process_run[0].process.id
        else:
            raise Http404()
        return render(request, 'processindex.html',
                      {'username': request.user.userinfo.fullname, "errors": errors, "processrun_id": processrun_id,
                       "process_url": process_url, "process_name": process_name, "process_id": process_id,
                       "s_tag": s_tag})
    else:
        return HttpResponseRedirect("/login")


def get_process_index_data(request):
    """
    流程领导页面数据构造
    :param request:
    :return:
    """
    if request.user.is_authenticated():
        processrun_id = request.POST.get("p_run_id", "")

        current_processruns = ProcessRun.objects.filter(
            id=int(processrun_id)).select_related("process")

        if current_processruns:
            current_processrun = current_processruns[0]
            current_process = current_processrun.process
            # 流程信息
            c_process_run_state = current_processrun.state
            process_name = current_process.name
            starttime = current_processrun.starttime
            endtime = current_processrun.endtime
            rtoendtime = ""

            # 步骤信息
            # 遍历主流程,判断sub_process字段是否为complex
            # complex: 调用子步骤的state,starttime,endtime,percent,type
            # node/task: 步骤的state,starttime,endtime,percent,type
            c_process_steps = current_process.step_set.filter(state="1").filter(
                intertype__in=["complex", "node", "task"]).order_by("sort")

            steps = []
            rtostate = "RUN"

            # 主流程步骤(子流程/单步骤)
            pre_state = ""
            for c_num, step in enumerate(c_process_steps):
                if step.intertype == "complex":
                    sub_process_id = step.sub_process
                    c_process = Process.objects.filter(
                        id=int(sub_process_id)).filter(state="1")
                    if c_process.exists():
                        c_process = c_process[0]
                        # name
                        name = c_process.name
                        # state:DONE,RUN,ERROR,EDIT,STOP
                        # 根据第一个not_done步骤的状态来作为当前子流程状态
                        all_steps = c_process.step_set.filter(state="1").filter(
                            intertype__in=["node", "task"]).order_by("sort")
                        state = "EDIT"
                        c_step_run_index = 0
                        for num, first_not_done_step in enumerate(all_steps):
                            first_not_done_step_run = first_not_done_step.steprun_set.filter(
                                processrun=current_processrun)
                            if first_not_done_step_run:
                                first_not_done_step_run = first_not_done_step_run[
                                    0]
                                state = first_not_done_step_run.state
                                c_step_run_index = num
                                if first_not_done_step_run.state not in ["DONE", "EDIT"]:
                                    break
                        # starttime
                        first_step = c_process.step_set.filter(state="1").filter(
                            intertype__in=["node", "task"]).order_by("sort").first()
                        first_step_run = first_step.steprun_set.filter(
                            processrun=current_processrun)
                        if first_step_run:
                            first_step_run = first_step_run[0]
                            start_time = first_step_run.starttime
                        else:
                            start_time = None
                        # endtime
                        end_step = c_process.step_set.filter(state="1").filter(intertype__in=["node", "task"]).order_by(
                            "drwaid").last()
                        end_step_run = end_step.steprun_set.filter(
                            processrun=current_processrun)
                        if end_step_run:
                            end_step_run = end_step_run[0]
                            end_time = end_step_run.endtime
                        else:
                            end_time = None

                        # percent
                        if state == "DONE":
                            percent = "100"
                        else:
                            percent = "%02d" % (
                                    c_step_run_index / len(all_steps) * 100)
                        # type 当前运行子流程  *************************************
                        # 流程结束后的当前步骤 >> 最后一个步骤
                        type = ""
                        if c_process_run_state == "DONE" and c_num + 1 == len(c_process_steps):
                            type = "cur"
                        # 流程运行中的当前步骤
                        else:
                            if state not in ["DONE", "EDIT"]:
                                type = "cur"
                            # 没有RUN的判断
                            elif (pre_state == "" or pre_state == "DONE") and state == "EDIT":
                                type = "cur"
                            else:
                                type = ""
                        pre_state = state
                        # ****************************************

                        # delta_time
                        delta_time = 0
                        # c_tag
                        c_tag = "no"
                        steps.append({
                            "name": name,
                            "state": state,
                            "starttime": start_time.strftime('%Y-%m-%d %H:%M:%S') if start_time else None,
                            "endtime": end_time.strftime('%Y-%m-%d %H:%M:%S') if end_time else None,
                            "percent": percent,
                            "type": type,
                            "delta_time": delta_time,
                            "c_tag": c_tag,
                        })
                else:
                    name = step.name
                    c_step_run = step.steprun_set.filter(
                        processrun=current_processrun)
                    if c_step_run.exists():
                        c_step_run = c_step_run[0]
                        state = c_step_run.state
                        start_time = c_step_run.starttime
                        end_time = c_step_run.endtime

                        # percent
                        if c_step_run.state in ["DONE", "STOP"]:
                            percent = 100
                        else:
                            percent = 0

                        # c_tag判断 没有子步骤，不需要确认，有(长久执行)脚本的步骤
                        delta_time = 0
                        if c_step_run.verifyitemsrun_set.all().count() == 0 and c_step_run.scriptrun_set.all().exists():
                            now_time = datetime.datetime.now()
                            if not end_time and start_time:
                                delta_time = (now_time - start_time)
                                if delta_time:
                                    delta_time = "%.f" % delta_time.total_seconds()
                                else:
                                    delta_time = 0
                            c_tag = "yes"
                        else:
                            c_tag = "no"

                        # type
                        if state not in ["DONE", "EDIT"]:
                            type = "cur"
                        else:
                            type = ""

                        steps.append({
                            "name": name,
                            "state": state,
                            "starttime": start_time.strftime('%Y-%m-%d %H:%M:%S') if start_time else None,
                            "endtime": end_time.strftime('%Y-%m-%d %H:%M:%S') if end_time else None,
                            "percent": percent,
                            "type": type,
                            "delta_time": delta_time,
                            "c_tag": c_tag,
                        })

            # rtostate/rtoendtime RTO什么时候停止跳动?
            # 包含步骤："不计入RTO & 状态为CONFIRM/DONE"
            # 此时rtostate=DONE,rtoendtime为上一步结束时间;
            for step in c_process_steps:
                if step.intertype == "complex":
                    sub_process_id = step.sub_process
                    c_process = Process.objects.filter(
                        id=int(sub_process_id)).filter(state="1")
                    if c_process.exists():
                        c_process = c_process[0]
                        all_steps = c_process.step_set.filter(state="1").filter(
                            intertype__in=["node", "task"]).order_by("sort")
                        for sub_step in all_steps:
                            sub_step_run = sub_step.steprun_set.filter(
                                processrun=current_processrun)
                            if sub_step_run.exists():
                                sub_step_run = sub_step_run[0]
                                if sub_step_run.state in ["CONFIRM", "DONE"] and sub_step.rto_count_in == "0":
                                    rtostate = "DONE"
                                    break

                else:
                    c_step_run = step.steprun_set.filter(
                        processrun=current_processrun)
                    if c_step_run.exists():
                        c_step_run = c_step_run[0]
                        if c_step_run.state in ["CONFIRM", "DONE"] and step.rto_count_in == "0":
                            rtostate = "DONE"
                            break

            # rtoendtime
            # 构造所有步骤
            sub_processes = current_process.step_set.order_by("sort").filter(state="1").filter(
                intertype__in=["node", "task", "complex"]).values_list("sub_process", "intertype")
            total_list = []
            for sub_process in sub_processes:
                if sub_process[1] == "complex":
                    sub_process_id = sub_process[0]
                    c_process = Process.objects.filter(
                        id=int(sub_process_id)).filter(state="1")

                    mystep = c_process[0].step_set.order_by("sort").filter(state="1").filter(
                        intertype__in=["node", "task"])
                    for i in mystep:
                        total_list.append(i)
                else:
                    mystep = current_process.step_set.order_by("sort").filter(state="1").filter(
                        intertype__in=["node", "task"])
                    for i in mystep:
                        total_list.append(i)
            # 最后一个计入RTO的步骤的结束时间作为rtoendtime
            if rtostate == "DONE":
                for i in total_list:
                    if i.rto_count_in == "0":
                        break
                    i_step_run = i.steprun_set.filter(
                        processrun=current_processrun)
                    if i_step_run.exists():
                        i_step_run = i_step_run[0]
                        rtoendtime = i_step_run.endtime.strftime(
                            '%Y-%m-%d %H:%M:%S')

            # 流程需要签字
            if current_processrun.state == "SIGN":
                rtostate = "DONE"
                rtoendtime = current_processrun.starttime.strftime(
                    '%Y-%m-%d %H:%M:%S')

            # process_rate
            done_step_run = current_processrun.steprun_set.filter(state="DONE")
            if done_step_run.exists():
                done_num = len(done_step_run)
            else:
                done_num = 0
            process_rate = "%02d" % (
                    done_num / len(current_processrun.steprun_set.all()) * 100)

            current_time = datetime.datetime.now()
            c_step_run_data = {
                "current_time": current_time.strftime('%Y-%m-%d %H:%M:%S'),
                "name": process_name,
                "starttime": starttime.strftime('%Y-%m-%d %H:%M:%S') if starttime else "",
                "rtoendtime": rtoendtime,
                "endtime": endtime.strftime('%Y-%m-%d %H:%M:%S') if endtime else "",
                "state": c_process_run_state,
                "rtostate": rtostate,
                "percent": process_rate,
                "steps": steps
            }
        else:
            c_step_run_data = {}
        # with open(r"C:\Users\Administrator\Desktop\test.json", "w") as f:
        #     f.write(json.dumps(c_step_run_data))
        return JsonResponse(c_step_run_data)


def get_server_time_very_second(request):
    if request.user.is_authenticated():
        current_time = datetime.datetime.now()
        return JsonResponse({"current_time": current_time.strftime('%Y-%m-%d %H:%M:%S')})


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


def get_process_rto(request):
    if request.user.is_authenticated():
        # 不同流程最近的12次切换RTO
        all_processes = Process.objects.exclude(
            state="9").filter(type="falconstor", level="1")
        process_rto_list = []
        if all_processes:
            for process in all_processes:
                process_name = process.name
                processrun_rto_obj_list = process.processrun_set.filter(
                    state="DONE")
                current_rto_list = []
                for processrun_rto_obj in processrun_rto_obj_list:
                    current_rto = processrun_rto_obj.rto
                    current_rto = float("%.2f" % (current_rto / 60))

                    current_rto_list.append(current_rto)
                process_dict = {
                    "process_name": process_name,
                    "current_rto_list": current_rto_list,
                    "color": process.color
                }
                process_rto_list.append(process_dict)
        return JsonResponse({"data": process_rto_list if len(process_rto_list) <= 12 else process_rto_list[-12:]})


def get_daily_processrun(request):
    if request.user.is_authenticated():
        all_processrun_objs = ProcessRun.objects.filter(
            Q(state="DONE") | Q(state="STOP")).select_related("process")
        process_success_rate_list = []
        if all_processrun_objs:
            for process_run in all_processrun_objs:
                process_name = process_run.process.name
                start_time = process_run.starttime
                end_time = process_run.endtime
                process_color = process_run.process.color
                process_run_id = process_run.id
                # 进程url
                processrun_url = "/processindex/" + \
                                 str(process_run.id) + "?s=true"

                process_run_dict = {
                    "process_name": process_name,
                    "start_time": start_time,
                    "end_time": end_time,
                    "process_color": process_color,
                    "process_run_id": process_run_id,
                    "url": processrun_url,
                    "invite": "0"
                }
                process_success_rate_list.append(process_run_dict)
        all_process_run_invited = ProcessRun.objects.filter(
            state="PLAN").select_related("process")
        if all_process_run_invited:
            for process_run_invited in all_process_run_invited:
                invitations_dict = {
                    "process_name": process_run_invited.process.name,
                    "start_time": process_run_invited.starttime,
                    "end_time": process_run_invited.endtime,
                    "process_color": process_run_invited.process.color,
                    "process_run_id": process_run_invited.id,
                    "url": "/falconstorswitch/12",
                    "invite": "1"
                }
                process_success_rate_list.append(invitations_dict)
        return JsonResponse({"data": process_success_rate_list})


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
            app_select_list.append({
                "app_name": app.name,
                "id": app.id,
                "app_state": "selected" if app.id == current_app_id else ""
            })

        node["data"] = {"url": child.url,
                        "icon": child.icon,
                        "pname": parent.name,
                        "app_list": app_select_list,
                        "app_div_show": True if child.funtype == "fun" else False
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
                                funsave.save()

                                title = name
                        # 保存成功后，重新刷新页面，重新构造app_select_list
                        for c_app in all_app:
                            pre_app_select_list.append({
                                "app_name": c_app.name,
                                "id": c_app.id,
                                "app_state": "selected" if str(c_app.id) == app else ""
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
                        app_select_list.append({
                            "app_name": app.name,
                            "id": app.id,
                            "app_state": "selected" if app.id == current_app_id else ""
                        })

                    root["data"] = {"url": rootnode.url,
                                    "icon": rootnode.icon,
                                    "pname": "无",
                                    "app_list": app_select_list,
                                    "app_div_show": True if rootnode.funtype == "fun" else False
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
                                        profile = UserInfo()  # e*************************
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


def get_scene_tree(parent, selectid, allprocess):
    nodes = []
    children = parent.children.order_by("sort").exclude(state="9")
    for child in children:
        node = {}
        node["text"] = child.name
        node["id"] = child.id
        node["type"] = "org"
        noselectprocess = []
        selectprocess = []
        allselectprocess = child.process.exclude(state="9")
        myallprocess = []
        for process in allprocess:
            myallprocess.append(
                {"name": process.name, "id": process.id, "code": process.code})
            if process in allselectprocess:
                selectprocess.append(
                    {"name": process.name, "id": process.id, "code": process.code})
            else:
                noselectprocess.append(
                    {"name": process.name, "id": process.id, "code": process.code})

        node["data"] = {"code": child.code, "remark": child.remark, "business": child.business,
                        "application": child.application, "pname": parent.name,
                        "noselectprocess": noselectprocess, "selectprocess": selectprocess,
                        "myallprocess": myallprocess}
        node["children"] = get_scene_tree(child, selectid, allprocess)
        try:
            if int(selectid) == child.id:
                node["state"] = {"selected": True}
        except:
            pass
        nodes.append(node)
    return nodes


def scene(request, funid):
    """
    场景管理
    :param request:
    :param funid:
    :return:
    """
    if request.user.is_authenticated() and request.session['isadmin']:
        errors = []
        title = "请选择场景"
        selectid = ""
        id = ""
        pid = ""
        pname = ""
        noselectprocess = []
        selectprocess = []
        code = ""
        name = ""
        remark = ""
        business = ""
        application = ""
        # hiddendiv = "hidden"
        hiddendiv = "hidden"
        allprocess = Process.objects.filter(state="1", level=1)

        if request.method == 'POST':
            hiddendiv = ""
            id = request.POST.get('id')
            pid = request.POST.get('pid')
            try:
                id = int(id)

            except:
                raise Http404()
            try:
                pid = int(pid)
            except:
                raise Http404()
            if "save" in request.POST.keys():
                processlist = request.POST.getlist('my_multi_select1')
                noselectprocess = []
                selectprocess = []
                for process in allprocess:
                    if str(process.id) in processlist:
                        selectprocess.append(
                            {"name": process.name, "id": process.id, "code": process.code})
                    else:
                        noselectprocess.append(
                            {"name": process.name, "id": process.id, "code": process.code})
                pname = request.POST.get('pname')
                code = request.POST.get('code', '')
                name = request.POST.get('name', '')
                remark = request.POST.get('remark', '')
                business = request.POST.get('business', '')
                application = request.POST.get('application', '')

                if id == 0:
                    selectid = pid
                    title = "新建"
                    if code.strip() == '':
                        errors.append('场景编号不能为空。')
                    else:
                        if name.strip() == '':
                            errors.append('场景名称不能为空。')
                        else:
                            allscene = Scene.objects.exclude(
                                state="9").filter(code=code)
                            if (len(allscene) > 0):
                                errors.append('场景编号:' + code + '已存在。')
                            else:
                                try:
                                    newscene = Scene()
                                    newscene.code = code
                                    newscene.name = name
                                    newscene.remark = remark
                                    newscene.business = business
                                    newscene.application = application
                                    try:
                                        pscene = Scene.objects.get(id=pid)
                                    except:
                                        raise Http404()
                                    newscene.pnode = pscene
                                    sort = 1
                                    try:
                                        maxscene = Scene.objects.filter(
                                            pnode=pscene).latest('sort')
                                        sort = maxscene.sort + 1
                                    except:
                                        pass
                                    newscene.sort = sort
                                    newscene.save()
                                    for process in processlist:
                                        try:
                                            process = int(process)
                                            myprocess = allprocess.get(
                                                id=process)
                                            newscene.process.add(myprocess)
                                        except ValueError:
                                            raise Http404()
                                    title = name
                                    selectid = newscene.id
                                    id = newscene.id
                                except ValueError:
                                    errors.append('新增失败。')
                else:
                    selectid = id
                    title = name
                    if code.strip() == '':
                        errors.append('场景编号不能为空。')
                    else:
                        if name.strip() == '':
                            errors.append('场景名称不能为空。')
                        else:
                            allscene = Scene.objects.exclude(
                                state="9").filter(code=code)
                            if (len(allscene) > 0 and allscene[0].id != id):
                                errors.append('场景编号:' + code + '已存在。')
                            else:
                                try:
                                    scene = Scene.objects.get(id=id)
                                    scene.code = code
                                    scene.name = name
                                    scene.remark = remark
                                    scene.business = business
                                    scene.application = application
                                    scene.save()
                                    scene.process.clear()
                                    for process in processlist:
                                        try:
                                            process = int(process)
                                            myprocess = allprocess.get(
                                                id=process)
                                            scene.process.add(myprocess)
                                        except ValueError:
                                            raise Http404()
                                    title = name
                                except:
                                    errors.append('保存失败。')

        treedata = []
        rootnodes = Scene.objects.order_by(
            "sort").exclude(state="9").filter(pnode=None)
        if len(rootnodes) > 0:
            for rootnode in rootnodes:
                root = {}
                root["text"] = rootnode.name
                root["id"] = rootnode.id
                root["type"] = "org"
                myallprocess = []
                for process in allprocess:
                    myallprocess.append(
                        {"name": process.name, "id": process.id, "code": process.code})
                root["data"] = {"code": rootnode.code, "remark": rootnode.remark, "business": rootnode.business,
                                "noselectprocess": [], "selectprocess": [],
                                "application": rootnode.application, "pname": "无", "myallprocess": myallprocess}
                try:
                    if int(selectid) == rootnode.id:
                        root["state"] = {"opened": True, "selected": True}
                    else:
                        root["state"] = {"opened": True}
                except:
                    root["state"] = {"opened": True}
                root["children"] = get_scene_tree(
                    rootnode, selectid, allprocess)
                treedata.append(root)
        treedata = json.dumps(treedata)
        return render(request, 'scene.html',
                      {'username': request.user.userinfo.fullname, 'errors': errors, "id": id,
                       "pid": pid, "pname": pname, "name": name, "code": code, "remark": remark, "business": business,
                       "application": application,
                       "noselectprocess": noselectprocess, "selectprocess": selectprocess, "title": title,
                       "hiddendiv": hiddendiv, "treedata": treedata, "pagefuns": getpagefuns(funid)})
    else:
        return HttpResponseRedirect("/login")


def scenedel(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        if 'id' in request.POST:
            id = request.POST.get('id', '')
            try:
                id = int(id)
            except:
                raise Http404()
            scene = Scene.objects.get(id=id)
            scene.state = "9"
            scene.save()
            return HttpResponse(1)
        else:
            return HttpResponse(0)


def scenemove(request):
    if request.user.is_authenticated() and request.session['isadmin']:
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
            oldpscene = Scene.objects.get(id=old_parent)
            oldsort = old_position + 1
            oldscenes = Scene.objects.filter(
                pnode=oldpscene).filter(sort__gt=oldsort)

            pscene = Scene.objects.get(id=parent)
            sort = position + 1
            scenes = Scene.objects.filter(pnode=pscene).filter(
                sort__gte=sort).exclude(id=id)

            myscene = Scene.objects.get(id=id)
            scenesame = Scene.objects.filter(pnode=pscene).filter(
                name=myscene.name).exclude(id=id)
            if (len(scenesame) > 0):
                return HttpResponse("重名")
            else:
                if (len(oldscenes) > 0):
                    for oldscene in oldscenes:
                        try:
                            oldscene.sort = oldscene.sort - 1
                            oldscene.save()
                        except:
                            pass
                if (len(scenes) > 0):
                    for scene in scenes:
                        try:
                            scene.sort = scene.sort + 1
                            scene.save()
                        except:
                            pass
                try:
                    myscene.pnode = pscene
                    myscene.sort = sort
                    myscene.save()
                except:
                    pass
                if parent != old_parent:
                    return HttpResponse(pscene.name + "^" + str(pscene.id))
                else:
                    return HttpResponse("0")


def script(request, funid):
    if request.user.is_authenticated() and request.session['isadmin']:
        errors = []
        if request.method == 'POST':
            # 获取上传的文件，如果没有文件，则默认为None
            my_file = request.FILES.get("myfile", None)
            if not my_file:
                errors.append("请选择要导入的文件。")
            else:
                filetype = my_file.name.split(".")[-1]
                if filetype == "xls" or filetype == "xlsx":
                    myfilepath = os.path.join(os.path.join(
                        os.path.dirname(__file__), "upload\\temp"), my_file.name)
                    destination = open(myfilepath, 'wb+')
                    for chunk in my_file.chunks():  # 分块写入文件
                        destination.write(chunk)
                    destination.close()

                    data = xlrd.open_workbook(myfilepath)
                    sheet = data.sheets()[0]
                    rows = sheet.nrows
                    errors.append("导入成功。")
                    for i in range(rows):
                        if i > 0:
                            try:
                                allscript = Script.objects.filter(code=sheet.cell(i, 0).value).exclude(
                                    state="9").filter(step_id=None)
                                if (len(allscript) > 0):
                                    errors.append(sheet.cell(
                                        i, 0).value + ":已存在。")
                                else:
                                    ncols = sheet.ncols
                                    scriptsave = Script()
                                    scriptsave.code = sheet.cell(i, 0).value
                                    scriptsave.name = sheet.cell(i, 1).value
                                    scriptsave.ip = sheet.cell(i, 2).value
                                    # scriptsave.port = sheet.cell(i, 2).value
                                    scriptsave.type = sheet.cell(i, 3).value
                                    # scriptsave.runtype = sheet.cell(i, 4).value
                                    scriptsave.username = sheet.cell(
                                        i, 4).value
                                    scriptsave.password = sheet.cell(
                                        i, 5).value
                                    scriptsave.filename = sheet.cell(
                                        i, 6).value
                                    # scriptsave.paramtype = sheet.cell(i, 8).value
                                    # scriptsave.param = sheet.cell(i, 9).value
                                    scriptsave.scriptpath = sheet.cell(
                                        i, 7).value
                                    # scriptsave.runpath = sheet.cell(i, 11).value
                                    # scriptsave.maxtime = int(sheet.cell(i, 12).value)
                                    scriptsave.succeedtext = int(
                                        sheet.cell(i, 8).value)
                                    scriptsave.save()
                            except:
                                errors.append(sheet.cell(
                                    i, 0).value + ":数据存在问题，已剔除。")
                    os.remove(myfilepath)
                else:
                    errors.append("只能上传xls和xlsx文件，请选择正确的文件类型。")
        return render(request, 'script.html',
                      {'username': request.user.userinfo.fullname, "pagefuns": getpagefuns(funid, request=request),
                       "errors": errors})
    else:
        return HttpResponseRedirect("/login")


def scriptdata(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        result = []
        allscript = Script.objects.exclude(
            state="9").filter(step_id=None).values()
        if (len(allscript) > 0):
            for script in allscript:
                result.append(
                    {"id": script["id"], "code": script["code"], "name": script["name"], "ip": script["ip"],
                     "port": script["port"], "type": script["type"], "runtype": script["runtype"],
                     "username": script["username"], "password": script["password"], "filename": script["filename"],
                     "paramtype": script["paramtype"], "param": script["param"], "scriptpath": script["scriptpath"],
                     "runpath": script["runpath"], "maxtime": script["maxtime"], "time": script["time"],
                     "success_text": script["succeedtext"], "log_address": script["log_address"]})
        return HttpResponse(json.dumps({"data": result}))


def scriptdel(request):
    """
    当删除脚本管理中的脚本的同时，需要删除预案中绑定的脚本；
    :param request:
    :return:
    """
    if request.user.is_authenticated() and request.session['isadmin']:
        if 'id' in request.POST:
            id = request.POST.get('id', '')
            try:
                id = int(id)
            except:
                raise Http404()
            script = Script.objects.get(id=id)
            script.state = "9"
            script.save()

            script_code = script.code
            related_scripts = Script.objects.filter(code=script_code)
            for related_script in related_scripts:
                related_script.state = "9"
                related_script.save()

            return HttpResponse(1)
        else:
            return HttpResponse(0)


def scriptsave(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        if 'id' in request.POST:
            result = {}
            id = request.POST.get('id', '')
            code = request.POST.get('code', '')
            name = request.POST.get('name', '')
            ip = request.POST.get('ip', '')
            # port = request.POST.get('port', '')
            type = request.POST.get('type', '')
            # runtype = request.POST.get('runtype', '')
            username = request.POST.get('username', '')
            password = request.POST.get('password', '')
            filename = request.POST.get('filename', '')
            # paramtype = request.POST.get('paramtype', '')
            # param = request.POST.get('param', '')
            scriptpath = request.POST.get('scriptpath', '')
            # runpath = request.POST.get('runpath', '')
            # maxtime = request.POST.get('maxtime', '')
            # time = request.POST.get('time', '')
            success_text = request.POST.get('success_text', '')
            log_address = request.POST.get('log_address', '')
            try:
                id = int(id)
            except:
                raise Http404()
            if code.strip() == '':
                result["res"] = '脚本编码不能为空。'
            else:
                if name.strip() == '':
                    result["res"] = '脚本名称不能为空。'
                else:
                    if ip.strip() == '':
                        result["res"] = '主机IP不能为空。'
                    else:
                        # if port.strip() == '':
                        #     result["res"] = '端口号不能为空。'
                        # else:
                        if type.strip() == '':
                            result["res"] = '连接类型不能为空。'
                        else:
                            if username.strip() == '':
                                result["res"] = '用户名不能为空。'
                            else:
                                if password.strip() == '':
                                    result["res"] = '密码不能为空。'
                                else:
                                    if filename.strip() == '':
                                        result["res"] = '脚本文件名不能为空。'
                                    else:
                                        if scriptpath.strip() == '':
                                            result["res"] = '脚本文件路径不能为空。'
                                        else:
                                            # if runpath.strip() == '':
                                            #     result["res"] = '执行路径不能为空。'
                                            # else:
                                            #     if maxtime.strip() == '':
                                            #         result["res"] = '超时时间不能为空。'
                                            #     else:
                                            #         if time.strip() == '':
                                            #             result["res"] = '预计耗时不能为空。'
                                            #         else:
                                            # if success_text == '':
                                            #     result["res"] = 'SUCCESSTEXT不能为空。'
                                            # else:
                                            if id == 0:
                                                allscript = Script.objects.filter(code=code).exclude(
                                                    state="9").filter(step_id=None)
                                                if (len(allscript) > 0):
                                                    result["res"] = '脚本编码:' + \
                                                                    code + '已存在。'
                                                else:
                                                    scriptsave = Script()
                                                    scriptsave.code = code
                                                    scriptsave.name = name
                                                    scriptsave.ip = ip
                                                    # scriptsave.port = port
                                                    scriptsave.type = type
                                                    # scriptsave.runtype = runtype
                                                    scriptsave.username = username
                                                    scriptsave.password = password
                                                    scriptsave.filename = filename
                                                    # scriptsave.paramtype = paramtype
                                                    # scriptsave.param = param
                                                    scriptsave.scriptpath = scriptpath
                                                    scriptsave.succeedtext = success_text
                                                    scriptsave.log_address = log_address
                                                    # scriptsave.runpath = runpath
                                                    # try:
                                                    #     scriptsave.maxtime = int(maxtime)
                                                    # except:
                                                    #     pass
                                                    # try:
                                                    #     scriptsave.time = int(time)
                                                    # except:
                                                    #     pass
                                                    scriptsave.save()
                                                    result["res"] = "保存成功。"
                                                    result[
                                                        "data"] = scriptsave.id
                                            else:
                                                allscript = Script.objects.filter(code=code).exclude(
                                                    id=id).exclude(state="9").filter(step_id=None)
                                                if (len(allscript) > 0):
                                                    result["res"] = '脚本编码:' + \
                                                                    code + '已存在。'
                                                else:
                                                    try:
                                                        scriptsave = Script.objects.get(
                                                            id=id)
                                                        scriptsave.code = code
                                                        scriptsave.name = name
                                                        scriptsave.ip = ip
                                                        # scriptsave.port = port
                                                        scriptsave.type = type
                                                        # scriptsave.runtype = runtype
                                                        scriptsave.username = username
                                                        scriptsave.password = password
                                                        scriptsave.filename = filename
                                                        # scriptsave.paramtype = paramtype
                                                        # scriptsave.param = param
                                                        scriptsave.scriptpath = scriptpath
                                                        scriptsave.succeedtext = success_text
                                                        scriptsave.log_address = log_address
                                                        # scriptsave.runpath = runpath
                                                        # try:
                                                        #     scriptsave.maxtime = int(maxtime)
                                                        # except:
                                                        #     pass
                                                        # try:
                                                        #     scriptsave.time = int(time)
                                                        # except:
                                                        #     pass
                                                        scriptsave.save()
                                                        result["res"] = "保存成功。"
                                                        result[
                                                            "data"] = scriptsave.id
                                                    except:
                                                        result["res"] = "修改失败。"
            return HttpResponse(json.dumps(result))


def scriptexport(request):
    # do something...
    if request.user.is_authenticated():
        myfilepath = os.path.join(os.path.dirname(
            __file__), "upload\\temp\\scriptexport.xls")
        try:
            os.remove(myfilepath)
        except:
            pass
        filename = xlwt.Workbook()
        sheet = filename.add_sheet('sheet1')
        allscript = Script.objects.exclude(state="9").filter(step_id=None)
        sheet.write(0, 0, '脚本编号')
        sheet.write(0, 1, '脚本名称')
        sheet.write(0, 2, '主机IP')
        # sheet.write(0, 2, '端口号')
        sheet.write(0, 3, '连接类型')
        # sheet.write(0, 4, '运行类型')
        sheet.write(0, 4, '用户名')
        sheet.write(0, 5, '密码')
        sheet.write(0, 6, '脚本文件名')
        # sheet.write(0, 8, '参数类型')
        # sheet.write(0, 9, '脚本参数')
        sheet.write(0, 7, '脚本文件路径')
        # sheet.write(0, 11, '执行路径')
        # sheet.write(0, 12, '超时时间')
        # sheet.write(0, 13, '预计耗时')
        sheet.write(0, 8, 'SUCCESSTEXT')

        if len(allscript) > 0:
            for i in range(len(allscript)):
                sheet.write(i + 1, 0, allscript[i].code)
                sheet.write(i + 1, 1, allscript[i].name)
                sheet.write(i + 1, 2, allscript[i].ip)
                # sheet.write(i + 1, 2, allscript[i].port)
                sheet.write(i + 1, 3, allscript[i].type)
                # sheet.write(i + 1, 4, allscript[i].runtype)
                sheet.write(i + 1, 4, allscript[i].username)
                sheet.write(i + 1, 5, allscript[i].password)
                sheet.write(i + 1, 6, allscript[i].filename)
                # sheet.write(i + 1, 8, allscript[i].paramtype)
                # sheet.write(i + 1, 9, allscript[i].param)
                sheet.write(i + 1, 7, allscript[i].scriptpath)
                # sheet.write(i + 1, 11, allscript[i].runpath)
                # sheet.write(i + 1, 12, allscript[i].maxtime)
                # sheet.write(i + 1, 13, allscript[i].time)
                sheet.write(i + 1, 8, allscript[i].succeedtext)

        filename.save(myfilepath)

        the_file_name = "scriptexport.xls"
        response = StreamingHttpResponse(file_iterator(myfilepath))
        response['Content-Type'] = 'application/octet-stream; charset=unicode'
        response['Content-Disposition'] = 'attachment;filename="{0}"'.format(
            the_file_name)
        return response

    else:
        return HttpResponseRedirect("/login")


def processscriptsave(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        if 'id' in request.POST:
            result = {}
            processid = request.POST.get('processid', '')
            pid = request.POST.get('pid', '')
            id = request.POST.get('id', '')
            code = request.POST.get('code', '')
            name = request.POST.get('name', '')
            ip = request.POST.get('ip', '')
            type = request.POST.get('type', '')
            username = request.POST.get('username', '')
            password = request.POST.get('password', '')
            filename = request.POST.get('filename', '')
            scriptpath = request.POST.get('scriptpath', '')
            success_text = request.POST.get('success_text', '')
            log_address = request.POST.get('log_address', '')

            try:
                id = int(id)
                pid = int(pid)
                processid = int(processid)
            except:
                raise Http404()
            if code.strip() == '':
                result["res"] = '脚本编码不能为空。'
            else:
                if ip.strip() == '':
                    result["res"] = '主机IP不能为空。'
                else:
                    if name.strip() == '':
                        result["res"] = '脚本名称不能为空。'
                    else:
                        if type.strip() == '':
                            result["res"] = '连接类型不能为空。'
                        else:
                            if username.strip() == '':
                                result["res"] = '用户名不能为空。'
                            else:
                                if password.strip() == '':
                                    result["res"] = '密码不能为空。'
                                else:
                                    if filename.strip() == '':
                                        result["res"] = '脚本文件名不能为空。'
                                    else:
                                        if scriptpath.strip() == '':
                                            result["res"] = '脚本文件路径不能为空。'
                                        else:
                                            if id == 0:
                                                allscript = Script.objects.filter(code=code).exclude(
                                                    state="9").filter(step_id=pid)
                                                if (len(allscript) > 0):
                                                    result["res"] = '脚本编码:' + \
                                                                    code + '已存在。'
                                                else:
                                                    steplist = Step.objects.filter(
                                                        drwaid=pid, process_id=processid)
                                                    if len(steplist) > 0:
                                                        scriptsave = Script()
                                                        scriptsave.code = code
                                                        scriptsave.name = name
                                                        scriptsave.ip = ip
                                                        scriptsave.type = type
                                                        scriptsave.username = username
                                                        scriptsave.password = password
                                                        scriptsave.filename = filename
                                                        scriptsave.scriptpath = scriptpath
                                                        scriptsave.succeedtext = success_text
                                                        scriptsave.log_address = log_address
                                                        scriptsave.step = steplist[
                                                            0]
                                                        scriptsave.save()
                                                        result["res"] = "新增成功。"
                                                        result["data"] = str(
                                                            scriptsave.id).zfill(10)

                                            else:
                                                allscript = Script.objects.filter(code=code).exclude(
                                                    id=id).exclude(state="9").filter(step_id=pid)
                                                if (len(allscript) > 0):
                                                    result["res"] = '脚本编码:' + \
                                                                    code + '已存在。'
                                                else:
                                                    try:
                                                        scriptsave = Script.objects.get(
                                                            id=id)
                                                        scriptsave.code = code
                                                        scriptsave.name = name
                                                        scriptsave.ip = ip
                                                        scriptsave.type = type
                                                        scriptsave.username = username
                                                        scriptsave.password = password
                                                        scriptsave.filename = filename
                                                        scriptsave.scriptpath = scriptpath
                                                        scriptsave.succeedtext = success_text
                                                        scriptsave.log_address = log_address

                                                        scriptsave.save()
                                                        result["res"] = "修改成功。"
                                                        result["data"] = str(
                                                            scriptsave.id).zfill(10)
                                                    except:
                                                        result["res"] = "修改失败。"
            return HttpResponse(json.dumps(result))


def verify_items_save(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        if 'id' in request.POST:
            result = {}
            id = request.POST.get('id', '')
            name = request.POST.get('name', '')
            process_id = request.POST.get('processid', '')
            pid = request.POST.get("pid", "")
            try:
                id = int(id)
                pid = int(pid)
            except:
                raise Http404()

            if name.strip() == '':
                result["res"] = '名称不能为空。'
            else:
                if id == 0:
                    steplist = Step.objects.filter(
                        drwaid=pid, process_id=process_id)
                    verify_save = VerifyItems()
                    verify_save.name = name
                    verify_save.step = steplist[0]
                    verify_save.save()
                    result["res"] = "新增成功。"
                    result["data"] = str(verify_save.id).zfill(10)
                else:
                    try:
                        verify_save = VerifyItems.objects.get(id=id)
                        verify_save.name = name
                        verify_save.save()
                        result["res"] = "修改成功。"
                        result["data"] = str(verify_save.id).zfill(10)
                    except:
                        result["res"] = "修改失败。"
            return HttpResponse(json.dumps(result))


def get_verify_items_data(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        if 'id' in request.POST:
            id = request.POST.get('id', '')
            verify_id = request.POST.get("verify_id", "")

            try:
                id = int(id)
                verify_id = int(verify_id)
            except:
                raise Http404()
            all_verify_items = VerifyItems.objects.exclude(
                state="9").filter(id=verify_id)
            verify_data = ""
            if (len(all_verify_items) > 0):
                verify_data = {"id": str(all_verify_items[0].id).zfill(
                    10), "name": all_verify_items[0].name}
            return HttpResponse(json.dumps(verify_data))


def remove_verify_item(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        # 移除当前步骤中的脚本关联
        verify_id = request.POST.get("verify_id", "")
        try:
            verify_id = int(verify_id)
        except:
            pass
        current_verify_item = VerifyItems.objects.filter(id=verify_id)
        if current_verify_item.exists():
            current_verify_item = current_verify_item[0]

            current_verify_item.state = "9"
            current_verify_item.save()
            return JsonResponse({
                "status": 1
            })
        else:
            return JsonResponse({
                "status": 0
            })


def get_script_data(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        if 'id' in request.POST:
            id = request.POST.get('id', '')
            script_id = request.POST.get("script_id", "")
            try:
                id = int(id)
                script_id = int(script_id)
            except:
                raise Http404()
            allscript = Script.objects.exclude(state="9").filter(id=script_id)
            script_data = ""
            if (len(allscript) > 0):
                script_data = {"id": str(allscript[0].id).zfill(10), "code": allscript[0].code,
                               "name": allscript[0].name,
                               "ip": allscript[0].ip, "port": allscript[0].port, "type": allscript[0].type,
                               "runtype": allscript[0].runtype, "username": allscript[0].username,
                               "password": allscript[0].password, "filename": allscript[0].filename,
                               "paramtype": allscript[0].paramtype, "param": allscript[0].param,
                               "scriptpath": allscript[0].scriptpath, "success_text": allscript[0].succeedtext,
                               "runpath": allscript[0].runpath, "maxtime": allscript[0].maxtime,
                               "time": allscript[0].time, "log_address": allscript[0].log_address}
            return HttpResponse(json.dumps(script_data))


def remove_script(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        # 移除当前步骤中的脚本关联
        script_id = request.POST.get("script_id", "")
        try:
            script_id = int(script_id)
        except:
            pass

        current_script = Script.objects.filter(id=script_id).exclude(state="9")
        if current_script.exists():
            current_script = current_script[0]

            current_script.state = "9"
            current_script.save()
            return JsonResponse({
                "status": 1
            })
        else:
            return JsonResponse({
                "status": 0
            })


def processdrawrelease(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        if request.method == 'POST':
            pid = request.POST.get('id', '')
            try:
                pid = int(pid)
            except:
                raise Http404()
            myprocess = Process.objects.get(id=pid)
            myprocess.state = "1"
            myprocess.save()
            return HttpResponse("发布成功！")


def processdrawtest(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        if request.method == 'POST':
            pid = request.POST.get('id', '')
            try:
                pid = int(pid)
            except:
                raise Http404()
            myprocess = Process.objects.get(id=pid)
            allstep = myprocess.step_set.exclude(state="9")
            if (len(allstep) <= 0):
                return HttpResponse("流程下未发现任何可用步骤，请检查流程配置是否正确。")
            allstart = allstep.filter(intertype__contains="start")
            if (len(allstart) <= 0):
                return HttpResponse("未发现开始节点，流程中必须存在开始节点。")
            if (len(allstart) > 1):
                return HttpResponse("发现多个开始节点，流程中只能存在一个开始节点。")
            startlineto = allstep.filter(
                type='lines', tonode='demo_node_' + str(allstart[0].drwaid).zfill(10))
            if (len(startlineto) > 0):
                return HttpResponse("开始节点不能作为连线终点。")
            startlinefrom = allstep.filter(
                type='lines', fromnode='demo_node_' + str(allstart[0].drwaid).zfill(10))
            if (len(startlinefrom) < 1):
                return HttpResponse("必须存在以开始节点为起点的连线。")

            allend = allstep.filter(intertype__contains="end")
            if (len(allend) <= 0):
                return HttpResponse("未发现结束节点，流程中必须存在结束节点。")
            if (len(allend) > 1):
                return HttpResponse("发现多个结束节点，流程中只能存在一个结束节点。")
            endlinefrom = allstep.filter(
                type='lines', fromnode='demo_node_' + str(allend[0].drwaid).zfill(10))
            if (len(endlinefrom) > 0):
                return HttpResponse("结束节点不能作为连线起点。")
            endlineto = allstep.filter(
                type='lines', tonode='demo_node_' + str(allend[0].drwaid).zfill(10))
            if (len(endlineto) < 1):
                return HttpResponse("必须存在以结束节点为终点的连线。")

            allnodes = allstep.filter(type='nodes').exclude(intertype__contains="start").exclude(
                intertype__contains="end")
            if len(allnodes) > 0:
                for allnode in allnodes:
                    linefrom = allstep.filter(
                        type='lines', fromnode='demo_node_' + str(allnode.drwaid).zfill(10))
                    if (len(linefrom) <= 0):
                        return HttpResponse("节点" + allnode.name + "必须连接下一步。")
                    lineto = allstep.filter(
                        type='lines', tonode='demo_node_' + str(allnode.drwaid).zfill(10))
                    if (len(lineto) <= 0):
                        return HttpResponse("节点" + allnode.name + "必须连接上一步。")
            return HttpResponse("验证通过")


def processcopy(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        if 'id' in request.POST:
            result = {}
            id = request.POST.get('id', '')
            code = request.POST.get('code', '')
            name = request.POST.get('name', '')
            rto = request.POST.get('rto', '')
            rpo = request.POST.get('rpo', '')
            remark = request.POST.get('remark', '')
            sign = request.POST.get('sign', '')
            sort = request.POST.get('sort', '')
            color = request.POST.get('color', '')
            try:
                id = int(id)
            except:
                raise Http404()
            if code.strip() == '':
                result["res"] = '新预案编码不能为空。'
            else:
                if name.strip() == '':
                    result["res"] = '新预案名称不能为空。'
                else:
                    allprocess = Process.objects.filter(
                        code=code).exclude(state="9")
                    if (len(allprocess) > 0):
                        result["res"] = '预案编码:' + code + '已存在。'
                    else:
                        processold = Process.objects.get(id=id)
                        processsave = Process()
                        processsave.code = code
                        processsave.name = name
                        try:
                            processsave.rto = int(rto)
                        except:
                            pass
                        try:
                            processsave.rpo = int(rpo)
                        except:
                            pass
                        processsave.remark = remark
                        processsave.sign = sign
                        processsave.sort = sort
                        processsave.color = color
                        processsave.color = processold.url
                        processsave.color = processold.type
                        processsave.color = processold.state
                        processsave.save()

                        allstep = processold.step_set.all()
                        if (len(allstep) > 0):
                            for step in allstep:
                                savestep = Step()
                                savestep.process = processsave
                                savestep.code = step.code
                                savestep.name = step.name
                                savestep.approval = step.approval
                                savestep.type = step.type
                                savestep.skip = step.skip
                                savestep.group = step.group
                                savestep.time = step.time
                                savestep.formula = step.formula
                                savestep.state = step.state
                                savestep.sort = step.sort
                                savestep.drwaid = step.drwaid
                                savestep.left = step.left
                                savestep.top = step.top
                                savestep.intertype = step.intertype
                                savestep.width = step.width
                                savestep.height = step.height
                                savestep.fromnode = step.fromnode
                                savestep.tonode = step.tonode
                                savestep.rto_count_in = step.rto_count_in
                                savestep.remark = step.remark
                                savestep.sub_process = step.sub_process
                                savestep.save()

                                allscript = step.script_set.all()
                                if (len(allscript) > 0):
                                    for script in allscript:
                                        scriptsave = Script()
                                        scriptsave.code = script.code
                                        scriptsave.name = script.name
                                        scriptsave.ip = script.ip
                                        scriptsave.type = script.type
                                        scriptsave.username = script.username
                                        scriptsave.password = script.password
                                        scriptsave.filename = script.filename
                                        scriptsave.scriptpath = script.scriptpath
                                        scriptsave.time = script.time
                                        scriptsave.state = script.state
                                        scriptsave.sort = script.sort
                                        scriptsave.succeedtext = script.succeedtext
                                        scriptsave.log_address = script.log_address
                                        scriptsave.step = savestep
                                        scriptsave.save()

                        result["res"] = "复制成功。"
                        result["data"] = processsave.id
            return HttpResponse(json.dumps(result))


def setpsave(request):
    if request.method == 'POST':
        result = ""
        id = request.POST.get('id', '')
        pid = request.POST.get('pid', '')
        name = request.POST.get('name', '')
        time = request.POST.get('time', '')
        skip = request.POST.get('skip', '')
        approval = request.POST.get('approval', '')
        group = request.POST.get('group', '')
        rto_count_in = request.POST.get('rto_count_in', '')
        remark = request.POST.get('remark', '')

        process_id = request.POST.get('process_id', '')
        try:
            id = int(id)
        except:
            raise Http404()
        data = ""
        # 新增步骤
        if id == 0:
            # process_name下右键新增
            try:
                pid = int(pid)
            except:
                pid = None
                max_sort_from_pnode = \
                    Step.objects.exclude(state="9").filter(pnode_id=None, process_id=process_id).aggregate(Max("sort"))[
                        "sort__max"]
            else:
                max_sort_from_pnode = \
                    Step.objects.exclude(state="9").filter(pnode_id=pid).filter(process_id=process_id).aggregate(
                        Max("sort"))["sort__max"]

            # 当前没有父节点
            if max_sort_from_pnode or max_sort_from_pnode == 0:
                my_sort = max_sort_from_pnode + 1
            else:
                my_sort = 0

            step = Step()
            step.skip = skip
            step.approval = approval
            step.group = group
            step.rto_count_in = rto_count_in
            step.time = time if time else None
            step.name = name
            step.process_id = process_id
            step.pnode_id = pid
            step.sort = my_sort
            step.remark = remark
            step.save()
            # last_id
            current_steps = Step.objects.filter(pnode_id=pid).exclude(state="9").order_by("sort").filter(
                process_id=process_id)
            last_id = current_steps[0].id
            for num, step in enumerate(current_steps):
                if num == 0:
                    step.last_id = ""
                else:
                    step.last_id = last_id
                last_id = step.id
                step.save()
            result = "保存成功。"
            data = step.id
        else:
            step = Step.objects.filter(id=id)
            if (len(step) > 0):
                step[0].name = name
                try:
                    time = int(time)
                    step[0].time = time
                except:
                    pass
                step[0].skip = skip
                step[0].approval = approval
                step[0].group = group
                step[0].rto_count_in = rto_count_in
                step[0].remark = remark
                step[0].save()
                result = "保存成功。"
            else:
                result = "当前步骤不存在，请联系客服！"
            # else:
            #     step = Step()
            #     step[0].name = name
            #     try:
            #         time = int(time)
            #         step[0].time = time
            #     except:
            #         pass
            #     step.skip = skip
            #     step.approval = approval
            #     step.group = group
            #     step.rto_count_in = rto_count_in
            #     step.remark = remark
            #     step.save()
            #     result = "保存成功。"
        return JsonResponse({
            "result": result,
            "data": data
        })


def custom_step_tree(request):
    if request.user.is_authenticated():
        errors = []
        id = request.POST.get('id', "")
        p_step = ""
        pid = request.POST.get('pid', "")
        name = request.POST.get('name', "")
        process_id = request.POST.get("process", "")
        current_process = Process.objects.filter(id=process_id)
        if current_process:
            current_process = current_process[0]
        else:
            raise Http404()
        process_name = current_process.name

        if id == 0:
            selectid = pid
            title = "新建"
        else:
            selectid = id
            title = name

        try:
            if id == 0:
                sort = 1
                try:
                    maxstep = Step.objects.filter(
                        pnode=p_step).latest('sort').exclude(state="9")
                    sort = maxstep.sort + 1
                except:
                    pass
                funsave = Step()
                funsave.pnode = p_step
                funsave.name = name
                funsave.sort = sort
                funsave.save()
                title = name
                id = funsave.id
                selectid = id
            else:
                funsave = Step.objects.get(id=id)
                funsave.name = name
                funsave.save()
                title = name
        except:
            errors.append('保存失败。')

        treedata = []
        rootnodes = Step.objects.order_by("sort").filter(
            process_id=process_id, pnode=None).exclude(state="9")

        all_groups = Group.objects.exclude(state="9")
        group_string = "" + "+" + " -------------- " + "&"
        for group in all_groups:
            id_name_plus = str(group.id) + "+" + str(group.name) + "&"
            group_string += id_name_plus
        if len(rootnodes) > 0:
            for rootnode in rootnodes:
                root = {}
                scripts = rootnode.script_set.exclude(state="9")
                script_string = ""
                for script in scripts:
                    id_code_plus = str(script.id) + "+" + \
                                   str(script.name) + "&"
                    script_string += id_code_plus

                verify_items_string = ""
                verify_items = rootnode.verifyitems_set.exclude(state="9")
                for verify_item in verify_items:
                    id_name_plus = str(verify_item.id) + \
                                   "+" + str(verify_item.name) + "&"
                    verify_items_string += id_name_plus
                root["text"] = rootnode.name
                root["id"] = rootnode.id
                group_name = ""
                if rootnode.group:
                    group_id = rootnode.group
                    group_name = Group.objects.filter(id=group_id)[0].name
                root["data"] = {"time": rootnode.time, "approval": rootnode.approval, "skip": rootnode.skip,
                                "allgroups": group_string, "group": rootnode.group, "group_name": group_name,
                                "scripts": script_string, "errors": errors, "title": title,
                                "rto_count_in": rootnode.rto_count_in, "remark": rootnode.remark,
                                "verifyitems": verify_items_string}
                root["children"] = get_step_tree(rootnode, selectid)
                root["state"] = {"opened": True}
                treedata.append(root)
        process = {}
        process["text"] = process_name
        process["data"] = {"allgroups": group_string, "verify": "first_node"}
        process["children"] = treedata
        process["state"] = {"opened": True}
        return JsonResponse({"treedata": process})
    else:
        return HttpResponseRedirect("/login")


def processconfig(request, funid):
    if request.user.is_authenticated():
        process_id = request.GET.get("process_id", "")
        if process_id:
            process_id = int(process_id)

        processes = Process.objects.exclude(state="9").order_by(
            "sort").filter(type="falconstor")
        processlist = []
        for process in processes:
            processlist.append(
                {"id": process.id, "code": process.code, "name": process.name})
        return render(request, 'processconfig.html',
                      {'username': request.user.userinfo.fullname, "pagefuns": getpagefuns(funid, request=request),
                       "processlist": processlist, "process_id": process_id})


def del_step(request):
    if request.user.is_authenticated():
        if 'id' in request.POST:
            id = request.POST.get('id', '')
            process_id = request.POST.get('process_id', '')
            try:
                id = int(id)
            except:
                raise Http404()
            try:
                process_id = int(process_id)
            except:
                raise Http404()
            allsteps = Step.objects.filter(id=id)
            if (len(allsteps) > 0):
                sort = allsteps[0].sort
                pstep = allsteps[0].pnode
                allsteps[0].state = 9
                allsteps[0].save()
                sortsteps = Step.objects.filter(pnode=pstep).filter(sort__gt=sort).exclude(state="9").filter(
                    process_id=process_id)
                if len(sortsteps) > 0:
                    for sortstep in sortsteps:
                        try:
                            sortstep.sort = sortstep.sort - 1
                            sortstep.save()
                        except:
                            pass

                current_pnode_id = allsteps[0].pnode_id
                # last_id
                current_steps = Step.objects.filter(pnode_id=current_pnode_id).exclude(state="9").order_by(
                    "sort").filter(
                    process_id=process_id)
                if current_steps:
                    last_id = current_steps[0].id
                    for num, step in enumerate(current_steps):
                        if num == 0:
                            step.last_id = ""
                        else:
                            step.last_id = last_id
                        last_id = step.id
                        step.save()

                return HttpResponse(1)
            else:
                return HttpResponse(0)


def move_step(request):
    if request.user.is_authenticated():
        if 'id' in request.POST:
            id = request.POST.get('id', '')
            parent = request.POST.get('parent', '')
            old_parent = request.POST.get('old_parent', '')
            old_position = request.POST.get('old_position', '')
            position = request.POST.get('position', '')
            process_id = request.POST.get('process_id', '')
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

            cur_step_obj = \
                Step.objects.filter(pnode_id=old_parent).filter(sort=old_position).filter(
                    process_id=process_id).exclude(state="9")[0]
            cur_step_obj.sort = position
            cur_step_id = cur_step_obj.id
            cur_step_obj.save()
            # 同一pnode
            if parent == old_parent:
                # 向上拽
                steps_under_pnode = Step.objects.filter(pnode_id=old_parent).exclude(state="9").filter(
                    sort__gte=position,
                    sort__lt=old_position).exclude(
                    id=cur_step_id).filter(process_id=process_id)
                for step in steps_under_pnode:
                    step.sort += 1
                    step.save()

                # 向下拽
                steps_under_pnode = Step.objects.filter(pnode_id=old_parent).exclude(state="9").filter(
                    sort__gt=old_position, sort__lte=position).exclude(id=cur_step_id).filter(process_id=process_id)
                for step in steps_under_pnode:
                    step.sort -= 1
                    step.save()

            # 向其他节点拽
            else:
                # 原来pnode下
                old_steps = Step.objects.filter(pnode_id=old_parent).exclude(state="9").filter(
                    sort__gt=old_position).exclude(id=cur_step_id).filter(process_id=process_id)
                for step in old_steps:
                    step.sort -= 1
                    step.save()
                # 后来pnode下
                cur_steps = Step.objects.filter(pnode_id=parent).exclude(state="9").filter(sort__gte=position).exclude(
                    id=cur_step_id).filter(process_id=process_id)
                for step in cur_steps:
                    step.sort += 1
                    step.save()

            # pnode
            if parent:
                parent_step = Step.objects.get(id=parent)
            else:
                parent_step = None
            mystep = Step.objects.get(id=id)
            try:
                mystep.pnode = parent_step
                mystep.save()
            except:
                pass

            # last_id
            old_steps = Step.objects.filter(pnode_id=old_parent).exclude(state="9").order_by("sort").filter(
                process_id=process_id)
            if old_steps:
                last_id = old_steps[0].id
                for num, step in enumerate(old_steps):
                    if num == 0:
                        step.last_id = ""
                    else:
                        step.last_id = last_id
                    last_id = step.id
                    step.save()
            after_steps = Step.objects.filter(pnode_id=parent).exclude(state="9").order_by("sort").filter(
                process_id=process_id)
            if after_steps:
                last_id = after_steps[0].id
                for num, step in enumerate(after_steps):
                    if num == 0:
                        step.last_id = ""
                    else:
                        step.last_id = last_id
                    last_id = step.id
                    step.save()

            if parent != old_parent:
                if parent == None:
                    return HttpResponse(" ^ ")
                else:
                    return HttpResponse(parent_step.name + "^" + str(parent_step.id))
            else:
                return HttpResponse("0")


def get_all_groups(request):
    if request.user.is_authenticated():
        all_group_list = []
        all_groups = Group.objects.exclude(state="9")
        for num, group in enumerate(all_groups):
            group_info_dict = {
                "group_id": group.id,
                "group_name": group.name,
            }
            all_group_list.append(group_info_dict)
        return JsonResponse({"data": all_group_list})


def process_design(request, funid):
    if request.user.is_authenticated():
        return render(request, "processdesign.html",
                      {'username': request.user.userinfo.fullname, "pagefuns": getpagefuns(funid, request=request)})


def process_data(request):
    """
    区分子父流程/默认流程
    :param request:
    :return:
    """
    if request.user.is_authenticated() and request.session['isadmin']:
        process_level = request.GET.get("process_level", "")
        result = []
        if not process_level or process_level == "0":
            all_process = Process.objects.exclude(state="9").filter(
                type="falconstor").order_by("sort")
        else:
            all_process = Process.objects.exclude(state="9").filter(type="falconstor",
                                                                    level=int(process_level)).order_by(
                "sort")
        if all_process.exists():
            for process in all_process:
                result.append({
                    "process_id": process.id,
                    "process_code": process.code,
                    "process_name": process.name,
                    "process_remark": process.remark,
                    "process_sign": process.sign,
                    "process_rto": process.rto,
                    "process_rpo": process.rpo,
                    "process_sort": process.sort,
                    "process_color": process.color,
                    "process_level_key": process.level,
                    "process_level_value": process.get_level_display(),
                    "process_state": "已发布" if process.state == "1" else "未发布",
                })
        return JsonResponse({"data": result})


def process_save(request):
    if request.user.is_authenticated() and request.session['isadmin']:
        if 'id' in request.POST:
            result = {}
            id = request.POST.get('id', '')
            code = request.POST.get('code', '')
            name = request.POST.get('name', '')
            remark = request.POST.get('remark', '')
            sign = request.POST.get('sign', '')
            rto = request.POST.get('rto', '')
            rpo = request.POST.get('rpo', '')
            sort = request.POST.get('sort', '')
            color = request.POST.get('color', '')
            level = request.POST.get('level', '')
            try:
                id = int(id)
            except:
                raise Http404()
            if code.strip() == '':
                result["res"] = '预案编码不能为空。'
            else:
                if name.strip() == '':
                    result["res"] = '预案名称不能为空。'
                else:
                    if level.strip() == "":
                        result["res"] = '流程级别不能为空。'
                    else:
                        if sign.strip() == '':
                            result["res"] = '是否签到不能为空。'
                        else:
                            if id == 0:
                                all_process = Process.objects.filter(code=code).exclude(
                                    state="9").filter(type="falconstor")
                                if (len(all_process) > 0):
                                    result["res"] = '预案编码:' + code + '已存在。'
                                else:
                                    processsave = Process()
                                    processsave.url = '/falconstor'
                                    processsave.type = 'falconstor'
                                    processsave.code = code
                                    processsave.name = name
                                    processsave.remark = remark
                                    processsave.sign = sign
                                    processsave.rto = rto if rto else None
                                    processsave.rpo = rpo if rpo else None
                                    processsave.sort = sort if sort else None
                                    processsave.color = color
                                    processsave.level = level
                                    processsave.state = "0"
                                    processsave.save()
                                    result["res"] = "保存成功。"
                                    result["data"] = processsave.id
                            else:
                                all_process = Process.objects.filter(
                                    id=id).exclude(state="9")
                                if all_process.exists():
                                    try:
                                        processsave = Process.objects.get(
                                            id=id)
                                        processsave.code = code
                                        processsave.name = name
                                        processsave.remark = remark
                                        processsave.sign = sign
                                        processsave.rto = rto if rto else None
                                        processsave.rpo = rpo if rpo else None
                                        processsave.sort = sort if sort else None
                                        processsave.color = color
                                        processsave.level = level
                                        processsave.save()
                                        result["res"] = "保存成功。"
                                        result["data"] = processsave.id
                                    except:
                                        result["res"] = "修改失败。"
                                else:
                                    result["res"] = "预案不存在"
        return HttpResponse(json.dumps(result))


def process_del(request):
    if request.user.is_authenticated():
        if 'id' in request.POST:
            id = request.POST.get('id', '')
            try:
                id = int(id)
            except:
                raise Http404()
            process = Process.objects.get(id=id)
            process.state = "9"
            process.save()

            return HttpResponse(1)
        else:
            return HttpResponse(0)


def processdraw(request, offset, funid):
    if request.user.is_authenticated() and request.session['isadmin']:
        try:
            id = int(offset)
        except:
            raise Http404()
        process = Process.objects.get(id=id)
        allprocess = Process.objects.exclude(
            state="9").filter(type="falconstor", level=2)
        allgroup = Group.objects.exclude(state="9")
        return render(request, 'processdraw.html',
                      {'username': request.user.last_name + request.user.first_name, "allprocess": allprocess,
                       "allgroup": allgroup, "pagefuns": getpagefuns(funid),
                       "name": process.name, "id": process.id, "offset": offset, "sidebarclosed": True})
    else:
        return HttpResponseRedirect("/login")


def getprocess(request):
    if request.method == 'GET':
        pid = request.GET.get('id')
        try:
            pid = int(pid)
        except:
            raise Http404()
        result = {}
        myprocess = Process.objects.filter(id=pid)

        if myprocess.exists():
            myprocess = myprocess[0]
        else:
            raise Http404()

        result["title"] = myprocess.id
        result["nodes"] = {}
        result["lines"] = {}
        result["areas"] = {}
        result["initNum"] = 1
        allstep = myprocess.step_set.exclude(state="9")
        if (len(allstep) > 0):
            allnode = allstep.filter(type="nodes")
            if (len(allnode) > 0):
                nodes = {}
                for node in allnode:
                    allscript = Script.objects.exclude(
                        state="9").filter(step=node).order_by("id")
                    stepscript = {}
                    if len(allscript) > 0:
                        for script in allscript:
                            stepscript["script_" + str(script.id).zfill(10)] = {"code": script.code, "ip": script.ip,
                                                                                "type": script.type,
                                                                                "runtype": script.runtype,
                                                                                "username": script.username,
                                                                                "password": script.password,
                                                                                "filename": script.filename,
                                                                                "scriptpath": script.scriptpath,
                                                                                }

                    verify_items = {}
                    all_verify_items = VerifyItems.objects.exclude(
                        state="9").filter(step=node).order_by("id")
                    if all_verify_items.exists():
                        for verify_item in all_verify_items:
                            verify_items["verify_" + str(verify_item.id).zfill(10)] = {
                                "verify_name": verify_item.name
                            }

                    nodes["demo_node_" + str(node.drwaid).zfill(10)] = {"name": node.name, "left": node.left,
                                                                        "top": node.top, "type": node.intertype,
                                                                        "width": node.width, "height": node.height,
                                                                        "alt": True, "skip": node.skip,
                                                                        "code": node.code, "group": node.group,
                                                                        "approval": node.approval,
                                                                        "rto_count_in": node.rto_count_in,
                                                                        "remark": node.remark,
                                                                        "verify_items": verify_items,
                                                                        "time": node.time, "stepscript": stepscript,
                                                                        "sub_process": node.sub_process}
                result["nodes"] = nodes
            allline = allstep.filter(type="lines")
            if (len(allline) > 0):
                lines = {}
                for line in allline:
                    lines["demo_line_" + str(line.drwaid).zfill(10)] = {"name": line.name, "from": line.fromnode,
                                                                        "to": line.tonode, "type": line.intertype,
                                                                        "alt": True, "formula": line.formula}
                result["lines"] = lines
            allarea = allstep.filter(type="areas")
            if (len(allarea) > 0):
                areas = {}
                for area in allarea:
                    areas["demo_area_" + str(area.drwaid).zfill(10)] = {"name": area.name, "left": area.left,
                                                                        "top": area.top, "color": area.intertype,
                                                                        "width": area.width, "height": area.height,
                                                                        "alt": True}
                result["areas"] = areas
            maxid = myprocess.step_set.latest('drwaid')
            result["initNum"] = maxid.drwaid + 1
        return HttpResponse(json.dumps({"data": result}))


def processdrawsave(request):
    """
    state:
        "1" 已发布
        "0" 未发布
        "9" 已删除
    :param request:
    :return:
    """
    if request.user.is_authenticated() and request.session['isadmin']:
        if request.method == 'POST':
            res = json.loads(request.body.decode())
            nodes = res["nodes"]
            lines = res["lines"]
            areas = res["areas"]
            pid = res["title"]
            try:
                pid = int(pid)
            except:
                raise Http404()

            # 如果流程已存在，设置成未发布状态
            myprocess = Process.objects.get(id=pid)
            # 重新载入步骤
            myprocess.step_set.exclude(state="9").update(state="9")
            myprocess.state = '0'
            myprocess.save()
            if len(nodes) > 0:
                nodeskeys = nodes.keys()
                if len(nodeskeys) > 0:
                    for num, nodeskey in enumerate(nodeskeys):
                        # 根据步骤位置id遍历，保存信息
                        drwaid = int(nodeskey.replace("demo_node_", ""))
                        mystep = myprocess.step_set.filter(drwaid=drwaid)
                        if (len(mystep) > 0):
                            try:
                                mystep[0].drwaid = drwaid
                            except:
                                pass

                            try:
                                mystep[0].name = nodes[nodeskey]["name"]
                            except:
                                pass
                            try:
                                mystep[0].left = nodes[nodeskey]["left"]
                            except:
                                pass
                            try:
                                mystep[0].top = nodes[nodeskey]["top"]
                            except:
                                pass
                            try:
                                mystep[0].intertype = nodes[nodeskey]["type"]
                            except:
                                pass
                            try:
                                mystep[0].width = nodes[nodeskey]["width"]
                            except:
                                pass
                            try:
                                mystep[0].height = nodes[nodeskey]["height"]
                            except:
                                pass
                            try:
                                mystep[0].skip = nodes[nodeskey]["skip"]
                            except:
                                pass
                            try:
                                mystep[0].code = nodes[nodeskey]["code"]
                            except:
                                pass
                            try:
                                mystep[0].group = nodes[nodeskey]["group"]
                            except:
                                pass
                            try:
                                if str(nodes[nodeskey]["time"]).strip():
                                    mystep[0].time = nodes[nodeskey]["time"]
                            except:
                                pass
                            try:
                                mystep[0].remark = nodes[nodeskey]["remark"]
                            except:
                                pass
                            try:
                                mystep[0].approval = nodes[
                                    nodeskey]["approval"]
                            except:
                                pass
                            try:
                                mystep[0].sub_process = nodes[
                                    nodeskey]["sub_process"]
                            except:
                                pass
                            try:
                                mystep[0].rto_count_in = nodes[
                                    nodeskey]["rto_count_in"]
                            except:
                                pass

                            mystep[0].state = "1"
                            mystep[0].save()
                        else:
                            savestep = Step()
                            savestep.drwaid = drwaid
                            try:
                                savestep.name = nodes[nodeskey]["name"]
                            except:
                                pass
                            try:
                                savestep.left = nodes[nodeskey]["left"]
                            except:
                                pass
                            try:
                                savestep.top = nodes[nodeskey]["top"]
                            except:
                                pass
                            try:
                                savestep.intertype = nodes[nodeskey]["type"]
                            except:
                                pass
                            try:
                                savestep.width = nodes[nodeskey]["width"]
                            except:
                                pass
                            try:
                                savestep.height = nodes[nodeskey]["height"]
                            except:
                                pass
                            try:
                                savestep.skip = nodes[nodeskey]["skip"]
                            except:
                                pass
                            try:
                                savestep.code = nodes[nodeskey]["code"]
                            except:
                                pass
                            try:
                                savestep.group = nodes[nodeskey]["group"]
                            except:
                                pass
                            try:
                                if str(nodes[nodeskey]["time"]).strip():
                                    savestep.time = nodes[nodeskey]["time"]
                            except:
                                pass
                            try:
                                savestep.remark = nodes[nodeskey]["remark"]
                            except:
                                pass
                            try:
                                savestep.approval = nodes[nodeskey]["approval"]
                            except:
                                pass
                            try:
                                savestep.sub_process = nodes[
                                    nodeskey]["sub_process"]
                            except:
                                pass
                            try:
                                mystep[0].rto_count_in = nodes[
                                    nodeskey]["rto_count_in"]
                            except:
                                pass

                            savestep.state = "1"
                            savestep.type = "nodes"
                            savestep.process = myprocess
                            savestep.save()

            if len(lines) > 0:
                lineskeys = lines.keys()
                if len(lineskeys) > 0:
                    for lineskey in lineskeys:
                        drwaid = int(lineskey.replace("demo_line_", ""))
                        mystep = myprocess.step_set.filter(drwaid=drwaid)
                        if (len(mystep) > 0):
                            try:
                                mystep[0].name = lines[lineskey]["name"]
                            except:
                                pass
                            try:
                                mystep[0].fromnode = lines[lineskey]["from"]
                            except:
                                pass
                            try:
                                mystep[0].tonode = lines[lineskey]["to"]
                            except:
                                pass
                            try:
                                mystep[0].intertype = lines[lineskey]["type"]
                            except:
                                pass
                            try:
                                mystep[0].formula = lines[lineskey]["formula"]
                            except:
                                pass
                            mystep[0].state = "1"
                            mystep[0].save()
                        else:
                            savestep = Step()
                            savestep.drwaid = drwaid
                            try:
                                savestep.name = lines[lineskey]["name"]
                            except:
                                pass
                            try:
                                savestep.fromnode = lines[lineskey]["from"]
                            except:
                                pass
                            try:
                                savestep.tonode = lines[lineskey]["to"]
                            except:
                                pass
                            try:
                                savestep.intertype = lines[lineskey]["type"]
                            except:
                                pass
                            try:
                                savestep.formula = lines[lineskey]["formula"]
                            except:
                                pass
                            savestep.state = "1"
                            savestep.type = "lines"
                            savestep.process = myprocess

                            savestep.save()
            if len(areas) > 0:
                areaskeys = areas.keys()
                if len(areaskeys) > 0:
                    for areaskey in areaskeys:
                        drwaid = int(areaskey.replace("demo_area_", ""))
                        mystep = myprocess.step_set.filter(drwaid=drwaid)
                        if (len(mystep) > 0):
                            try:
                                mystep[0].name = areas[areaskey]["name"]
                            except:
                                pass
                            try:
                                mystep[0].left = areas[areaskey]["left"]
                            except:
                                pass
                            try:
                                mystep[0].top = areas[areaskey]["top"]
                            except:
                                pass
                            try:
                                mystep[0].intertype = areas[areaskey]["color"]
                            except:
                                pass
                            try:
                                mystep[0].width = areas[areaskey]["width"]
                            except:
                                pass
                            try:
                                mystep[0].height = areas[areaskey]["height"]
                            except:
                                pass
                            mystep[0].state = "1"
                            mystep[0].save()
                        else:
                            savestep = Step()
                            savestep.drwaid = drwaid
                            try:
                                savestep.name = areas[areaskey]["name"]
                            except:
                                pass
                            try:
                                savestep.left = areas[areaskey]["left"]
                            except:
                                pass
                            try:
                                savestep.top = areas[areaskey]["top"]
                            except:
                                pass
                            try:
                                savestep.intertype = areas[areaskey]["color"]
                            except:
                                pass
                            try:
                                savestep.width = areas[areaskey]["width"]
                            except:
                                pass
                            try:
                                savestep.height = areas[areaskey]["height"]
                            except:
                                pass
                            savestep.state = "1"
                            savestep.type = "areas"
                            savestep.process = myprocess
                            savestep.save()

            # 将步骤存入一个sort排序字段取代drawid
            # 1.当前流程的start节点
            start_step = myprocess.step_set.filter(
                state="1", intertype__contains="start")[0]

            line_step = \
                myprocess.step_set.filter(state="1", type="lines",
                                          fromnode="demo_node_" + str(start_step.drwaid).zfill(10))[0]
            to_node = int(line_step.tonode.split("demo_node_")[1])
            current_step = \
                myprocess.step_set.filter(state="1", drwaid=to_node, intertype__in=[
                    "node", "task", "complex"])

            if current_step.exists():
                current_step = current_step[0]
                # 第一步
                current_step.sort = 0
                current_step.save()

                next_step = current_step
                # 循环后面步骤
                for i in range(1, len(nodes) + 1):
                    next_steps = sort_c_process_steps(myprocess, next_step)
                    if next_steps.exists():
                        next_step = next_steps[0]
                        next_step.sort = i
                        next_step.save()

            return HttpResponse("保存成功,请重新发布")


def falconstorswitch(request, process_id):
    """
    遍历主流程(子流程/主流程步骤)：
    1.子流程
        子流程名 wrapper_step_name
        子流程步骤 inner_step_list：
            确认项(名称) inner_verify_list(inner_verify_name)
            步骤名 inner_step_name
            用户组 inner_step_group_name
            脚本(名称)   inner_script_list
    2.主流程步骤
        确认项(名称) wrapper_verify_list(wrapper_verify_name)
        步骤名 wrapper_step_name
        用户组 wrapper_step_group_name
        脚本(名称) wrapper_script_list(wrapper_script_name)
    """
    if request.user.is_authenticated():
        # 遍历主流程(子流程/主流程步骤)
        wrapper_step_list = custom_wrapper_step_list(process_id)
        # 计划流程
        plan_process_run = ProcessRun.objects.filter(
            process_id=process_id, state="PLAN")
        if plan_process_run:
            plan_process_run = plan_process_run[0]
            plan_process_run_id = plan_process_run.id
        else:
            plan_process_run_id = ""

        # 根据url寻找到funid
        falconstor_url = "/falconstorswitch/{0}".format(process_id)

        c_fun = Fun.objects.filter(url=falconstor_url)
        if c_fun.exists():
            c_fun = c_fun[0]
            funid = str(c_fun.id)
        else:
            return Http404()
        return render(request, 'falconstorswitch.html',
                      {'username': request.user.userinfo.fullname, "pagefuns": getpagefuns(funid, request=request),
                       "wrapper_step_list": wrapper_step_list, "process_id": process_id,
                       "plan_process_run_id": plan_process_run_id})
    else:
        return HttpResponseRedirect("/login")


def falconstorswitchdata(request):
    if request.user.is_authenticated():
        result = []
        process_id = request.GET.get("process_id", "")
        state_dict = {
            "DONE": "已完成",
            "EDIT": "未执行",
            "RUN": "执行中",
            "ERROR": "执行失败",
            "IGNORE": "忽略",
            "STOP": "终止",
            "PLAN": "计划",
            "REJECT": "取消",
            "SIGN": "签到",
            "": "",
        }

        cursor = connection.cursor()

        exec_sql = """
        select r.starttime, r.endtime, r.creatuser, r.state, r.process_id, r.id, r.run_reason, p.name, p.url, p.type from faconstor_processrun as r 
        left join faconstor_process as p on p.id = r.process_id where r.state != '9' and r.state != 'REJECT' and r.process_id = {0} order by r.starttime desc;
        """.format(process_id)

        cursor.execute(exec_sql)
        rows = cursor.fetchall()
        for processrun_obj in rows:
            if processrun_obj[9] == "falconstor":
                create_users = processrun_obj[2] if processrun_obj[2] else ""
                create_user_objs = User.objects.filter(username=create_users)
                create_user_fullname = create_user_objs[
                    0].userinfo.fullname if create_user_objs else ""

                result.append({
                    "starttime": processrun_obj[0].strftime('%Y-%m-%d %H:%M:%S') if processrun_obj[0] else "",
                    "endtime": processrun_obj[1].strftime('%Y-%m-%d %H:%M:%S') if processrun_obj[1] else "",
                    "createuser": create_user_fullname,
                    "state": state_dict["{0}".format(processrun_obj[3])] if processrun_obj[3] else "",
                    "process_id": processrun_obj[4] if processrun_obj[4] else "",
                    "processrun_id": processrun_obj[5] if processrun_obj[5] else "",
                    "run_reason": processrun_obj[6][:20] if processrun_obj[6] else "",
                    "process_name": processrun_obj[7] if processrun_obj[7] else "",
                    "process_url": processrun_obj[8] if processrun_obj[8] else ""
                })
        return JsonResponse({"data": result})


def falconstorrun(request):
    """
    启动流程
    :param request:
    :return:
    """
    if request.user.is_authenticated():
        result = {}
        processid = request.POST.get('processid', '')
        run_person = request.POST.get('run_person', '')
        run_time = request.POST.get('run_time', '')
        run_reason = request.POST.get('run_reason', '')
        try:
            processid = int(processid)
        except:
            raise Http404()
        process = Process.objects.filter(id=processid).filter(
            state="1").filter(type="falconstor")
        if (len(process) <= 0):
            result["res"] = '流程启动失败，该流程不存在。'
        else:
            running_process = ProcessRun.objects.filter(
                process=process[0], state__in=["RUN", "ERROR"])
            if (len(running_process) > 0):
                result["res"] = '流程启动失败，该流程正在进行中，请勿重复启动。'
            else:
                planning_process = ProcessRun.objects.filter(
                    process=process[0], state="PLAN")
                if (len(planning_process) > 0):
                    result["res"] = '流程启动失败，计划流程未执行，务必先完成计划流程。'
                else:
                    myprocessrun = ProcessRun()
                    myprocessrun.process = process[0]
                    myprocessrun.starttime = datetime.datetime.now()
                    myprocessrun.creatuser = request.user.username
                    myprocessrun.run_reason = run_reason
                    myprocessrun.state = "RUN"
                    myprocessrun.DataSet_id = 89
                    myprocessrun.save()

                    # ************************************************* 1.子流程下所有步骤都要生成对应的StepRun.
                    mysteps = custom_all_steps(process[0])

                    if not mysteps:
                        result["res"] = '流程启动失败，没有找到可用步骤。'
                    else:
                        for num, step in enumerate(mysteps):
                            # 生成流程步骤
                            mysteprun = StepRun()
                            mysteprun.step = step
                            mysteprun.processrun = myprocessrun
                            mysteprun.state = "EDIT"
                            mysteprun.save()

                            myscript = step.script_set.exclude(state="9")
                            for script in myscript:
                                # 生成流程脚本
                                myscriptrun = ScriptRun()
                                myscriptrun.script = script
                                myscriptrun.steprun = mysteprun
                                myscriptrun.state = "EDIT"
                                myscriptrun.save()

                            myverifyitems = step.verifyitems_set.exclude(
                                state="9")
                            for verifyitems in myverifyitems:
                                # 生成流程确认项
                                myverifyitemsrun = VerifyItemsRun()
                                myverifyitemsrun.verify_items = verifyitems
                                myverifyitemsrun.steprun = mysteprun
                                myverifyitemsrun.save()

                        allgroup = process[0].step_set.exclude(state="9").exclude(Q(group="") | Q(group=None)).values(
                            "group").distinct()  # 过滤出需要签字的组,但一个对象只发送一次task

                        # 如果流程需要签字,发送签字tasks
                        if process[0].sign == "1" and len(allgroup) > 0:
                            # 将当前流程改成SIGN
                            c_process_run_id = myprocessrun.id
                            c_process_run = ProcessRun.objects.filter(
                                id=c_process_run_id)
                            if c_process_run:
                                c_process_run = c_process_run[0]
                                c_process_run.state = "SIGN"
                                c_process_run.save()

                            for group in allgroup:
                                try:
                                    signgroup = Group.objects.get(
                                        id=int(group["group"]))
                                    groupname = signgroup.name
                                    myprocesstask = ProcessTask()
                                    myprocesstask.processrun = myprocessrun
                                    myprocesstask.starttime = datetime.datetime.now()
                                    myprocesstask.senduser = request.user.username
                                    myprocesstask.receiveauth = group["group"]
                                    myprocesstask.type = "SIGN"
                                    myprocesstask.state = "0"
                                    myprocesstask.content = "流程即将启动”，请" + groupname + "签到。"
                                    myprocesstask.save()
                                except:
                                    pass
                            result["res"] = "新增成功。"
                            result["data"] = "/"

                        else:
                            prosssigns = ProcessTask.objects.filter(
                                processrun=myprocessrun, state="0")
                            if len(prosssigns) <= 0:
                                myprocesstask = ProcessTask()
                                myprocesstask.processrun = myprocessrun
                                myprocesstask.starttime = datetime.datetime.now()
                                myprocesstask.type = "INFO"
                                myprocesstask.logtype = "START"
                                myprocesstask.state = "1"
                                myprocesstask.senduser = request.user.username
                                myprocesstask.content = "流程已启动。"
                                myprocesstask.save()

                                exec_process.delay(myprocessrun.id)
                                result["res"] = "新增成功。"
                                result["data"] = "/processindex/" + \
                                                 str(myprocessrun.id)
        return HttpResponse(json.dumps(result))


def falconstor_run_invited(request):
    """
    启动邀请流程
    :param request:
    :return:
    """
    if request.user.is_authenticated() and request.session['isadmin']:
        result = {}
        process_id = request.POST.get('processid', '')
        run_person = request.POST.get('run_person', '')
        run_time = request.POST.get('run_time', '')
        run_reason = request.POST.get('run_reason', '')
        plan_process_run_id = request.POST.get('plan_process_run_id', '')

        current_process_run = ProcessRun.objects.filter(id=plan_process_run_id)

        if current_process_run:
            current_process_run = current_process_run[0]

            if current_process_run.state == "RUN":
                result["res"] = '请勿重复启动该流程。'
            else:
                current_process_run.starttime = datetime.datetime.now()
                current_process_run.creatuser = request.user.username
                current_process_run.run_reason = run_reason
                current_process_run.state = "RUN"
                current_process_run.DataSet_id = 89
                current_process_run.save()

                process = Process.objects.filter(id=process_id).exclude(
                    state="9").filter(type="falconstor")

                allgroup = process[0].step_set.exclude(state="9").exclude(Q(group="") | Q(group=None)).values(
                    "group").distinct()  # 过滤出需要签字的组,但一个对象只发送一次task

                # 如果流程需要签字,发送签字tasks
                if process[0].sign == "1" and len(allgroup) > 0:
                    # 将当前流程改成SIGN
                    c_process_run_id = current_process_run.id
                    c_process_run = ProcessRun.objects.filter(
                        id=c_process_run_id)
                    if c_process_run:
                        c_process_run = c_process_run[0]
                        c_process_run.state = "SIGN"
                        c_process_run.save()
                    for group in allgroup:
                        try:
                            signgroup = Group.objects.get(
                                id=int(group["group"]))
                            groupname = signgroup.name
                            myprocesstask = ProcessTask()
                            myprocesstask.processrun = current_process_run
                            myprocesstask.starttime = datetime.datetime.now()
                            myprocesstask.senduser = request.user.username
                            myprocesstask.receiveauth = group["group"]
                            myprocesstask.type = "SIGN"
                            myprocesstask.state = "0"
                            myprocesstask.content = "流程即将启动”，请" + groupname + "签到。"
                            myprocesstask.save()
                        except:
                            pass
                    result["res"] = "新增成功。"
                    result["data"] = "/"

                else:
                    prosssigns = ProcessTask.objects.filter(
                        processrun=current_process_run, state="0")
                    if len(prosssigns) <= 0:
                        myprocesstask = ProcessTask()
                        myprocesstask.processrun = current_process_run
                        myprocesstask.starttime = datetime.datetime.now()
                        myprocesstask.type = "INFO"
                        myprocesstask.logtype = "START"
                        myprocesstask.state = "1"
                        myprocesstask.senduser = request.user.username
                        myprocesstask.content = "流程已启动。"
                        myprocesstask.save()

                        exec_process.delay(current_process_run.id)
                        result["res"] = "新增成功。"
                        result["data"] = process[0].url + \
                                         "/" + str(current_process_run.id)
        else:
            result["res"] = '流程启动异常，请联系客服。'

        return HttpResponse(json.dumps(result))


def falconstor(request, offset, funid):
    if request.user.is_authenticated():
        id = 0
        try:
            id = int(offset)
        except:
            raise Http404()

        # 查看当前流程状态
        current_process_run = ProcessRun.objects.filter(id=offset)
        if current_process_run:
            current_process_run = current_process_run[0]
            current_run_state = current_process_run.state
        else:
            current_run_state = ""

        return render(request, 'falconstor.html',
                      {'username': request.user.userinfo.fullname, "process": id,
                       "current_run_state": current_run_state,
                       "pagefuns": getpagefuns(funid, request)})
    else:
        return HttpResponseRedirect("/index")


def getrunsetps(request):
    """
    获取运行流程步骤信息
    :param request:
    :return:
    """
    if request.user.is_authenticated():
        if request.method == 'POST':
            processresult = {}
            result = []
            process_name = ""
            process_state = ""
            process_starttime = ""
            process_endtime = ""
            process_note = ""
            process_rto = ""
            processrun = request.POST.get('process', '')
            try:
                processrun = int(processrun)
            except:
                raise Http404()
            processruns = ProcessRun.objects.exclude(
                state="9").filter(id=processrun)
            if len(processruns) > 0:
                process_name = processruns[0].process.name
                process_state = processruns[0].state
                process_note = processruns[0].note
                try:
                    process_starttime = processruns[0].starttime.strftime(
                        "%Y-%m-%d %H:%M:%S")
                except:
                    pass
                try:
                    process_endtime = processruns[0].endtime.strftime(
                        "%Y-%m-%d %H:%M:%S")
                except:
                    pass
                if process_state == "DONE" or process_state == "STOP":
                    try:
                        current_delta_time = (
                                processruns[0].endtime - processruns[0].starttime).total_seconds()
                        m, s = divmod(current_delta_time, 60)
                        h, m = divmod(m, 60)
                        process_rto = "%d时%02d分%02d秒" % (h, m, s)
                    except:
                        pass
                else:
                    start_time = processruns[0].starttime.replace(tzinfo=None)
                    current_time = datetime.datetime.now()
                    current_delta_time = (
                            current_time - start_time).total_seconds()
                    m, s = divmod(current_delta_time, 60)
                    h, m = divmod(m, 60)
                    process_rto = "%d时%02d分%02d秒" % (h, m, s)

                # 当前流程所有任务
                current_process_task_info = get_c_process_run_tasks(processrun)

                # process_rate
                done_step_run = processruns[0].steprun_set.filter(state="DONE")
                if done_step_run.exists():
                    done_num = len(done_step_run)
                else:
                    done_num = 0
                process_rate = "%02d" % (
                        done_num / len(processruns[0].steprun_set.all()) * 100)

                processresult["process_rate"] = process_rate
                processresult[
                    "current_process_task_info"] = current_process_task_info
                processresult["step"] = result
                processresult["process_name"] = process_name
                processresult["process_state"] = process_state
                processresult["process_starttime"] = process_starttime
                processresult["process_endtime"] = process_endtime
                processresult["process_note"] = process_note
                processresult["process_rto"] = process_rto

                # 1.遍历出子流程/步骤 如果是步骤,构造步骤信息 如果是子流程:name
                current_process = processruns[0].process
                c_process_steps = current_process.step_set.filter(state="1").filter(
                    intertype__in=["complex", "node", "task"]).order_by("sort")
                for step in c_process_steps:
                    runid = 0
                    starttime = ""
                    endtime = ""
                    operator = ""
                    parameter = ""
                    runresult = ""
                    explain = ""
                    state = ""
                    group = ""
                    note = ""
                    rto = 0
                    scripts = []
                    verifyitems = []
                    if step.intertype == "complex":
                        # 状态
                        sub_process = step.sub_process
                        sub_process_id = int(sub_process)
                        c_process = Process.objects.filter(
                            state="1", id=sub_process_id)
                        if c_process.exists():
                            c_process = c_process[0]
                            steps = c_process.step_set.filter(state="1", intertype__in=[
                                "node", "task", "complex"])
                            done_num = 0
                            run_num = 0
                            edit_num = 0
                            for c_step in steps:
                                c_step_run = c_step.steprun_set.filter(
                                    processrun=processruns[0])
                                if c_step_run.exists():
                                    c_step_run = c_step_run[0]
                                    # 完成
                                    if c_step_run.state == "DONE":
                                        done_num += 1
                                    # 运行
                                    if c_step_run.state in ["RUN", "ERROR", "CONFIRM"]:
                                        run_num += 1
                                    # 运行（没有RUN只有EDIT的时候）
                                    if c_step_run.state == "EDIT":
                                        edit_num += 1

                            if done_num == len(steps):
                                state = "DONE"
                            elif run_num > 0:
                                state = "RUN"
                            else:
                                state = ""
                    else:
                        # 步骤信息
                        steprunlist = step.steprun_set.filter(
                            processrun=processruns[0])
                        if len(steprunlist) > 0:
                            runid = steprunlist[0].id
                            try:
                                starttime = steprunlist[0].starttime.strftime(
                                    "%Y-%m-%d %H:%M:%S")
                            except:
                                pass
                            try:
                                endtime = steprunlist[0].endtime.strftime(
                                    "%Y-%m-%d %H:%M:%S")
                            except:
                                pass
                            rto = ""
                            if steprunlist[0].state == "DONE":
                                try:
                                    current_delta_time = (
                                            steprunlist[0].endtime - steprunlist[0].starttime).total_seconds()
                                    m, s = divmod(current_delta_time, 60)
                                    h, m = divmod(m, 60)
                                    rto = "%d时%02d分%02d秒" % (h, m, s)
                                except:
                                    pass
                            else:
                                start_time = steprunlist[0].starttime.replace(tzinfo=None) if steprunlist[
                                    0].starttime else ""
                                current_time = datetime.datetime.now()
                                current_delta_time = (
                                        current_time - start_time).total_seconds() if current_time and start_time else 0
                                m, s = divmod(current_delta_time, 60)
                                h, m = divmod(m, 60)
                                rto = "%d时%02d分%02d秒" % (h, m, s)
                            operator = steprunlist[0].operator
                            if operator is not None and operator != "":
                                try:
                                    curuser = User.objects.get(
                                        username=operator)
                                    operator = curuser.userinfo.fullname
                                except:
                                    pass
                            else:
                                operator = ""
                            parameter = steprunlist[0].parameter
                            runresult = steprunlist[0].result
                            explain = steprunlist[0].explain
                            state = steprunlist[0].state
                            note = steprunlist[0].note
                            group = step.group
                            try:
                                curgroup = Group.objects.get(id=int(group))
                                group = curgroup.name
                            except:
                                pass
                        # script
                        scriptlist = Script.objects.exclude(
                            state="9").filter(step=step)
                        for script in scriptlist:
                            runscriptid = 0
                            scriptstarttime = ""
                            scriptendtime = ""
                            scriptoperator = ""
                            scriptrunresult = ""
                            scriptexplain = ""
                            scriptrunlog = ""
                            scriptstate = ""
                            if len(steprunlist) > 0:
                                scriptrunlist = ScriptRun.objects.exclude(state="9").filter(steprun=steprunlist[0],
                                                                                            script=script)
                                if len(scriptrunlist) > 0:
                                    runscriptid = scriptrunlist[0].id
                                    try:
                                        scriptstarttime = scriptrunlist[0].starttime.strftime(
                                            "%Y-%m-%d %H:%M:%S")
                                    except:
                                        pass
                                    try:
                                        scriptendtime = scriptrunlist[0].endtime.strftime(
                                            "%Y-%m-%d %H:%M:%S")
                                    except:
                                        pass
                                    scriptoperator = scriptrunlist[0].operator
                                    scriptrunlog = scriptrunlist[0].runlog
                                    scriptrunresult = scriptrunlist[0].result
                                    scriptexplain = scriptrunlist[0].explain
                                    scriptstate = scriptrunlist[0].state
                            scripts.append(
                                {"id": script.id, "code": script.code, "name": script.name, "runscriptid": runscriptid,
                                 "scriptstarttime": scriptstarttime,
                                 "scriptendtime": scriptendtime, "scriptoperator": scriptoperator,
                                 "scriptrunresult": scriptrunresult, "scriptexplain": scriptexplain,
                                 "scriptrunlog": scriptrunlog, "scriptstate": scriptstate})
                        # verify_items
                        verifyitemslist = VerifyItems.objects.exclude(
                            state="9").filter(step=step)
                        for verifyitem in verifyitemslist:
                            runverifyitemid = 0
                            has_verified = ""
                            verifyitemstate = ""
                            if len(steprunlist) > 0:
                                verifyitemsrunlist = VerifyItemsRun.objects.exclude(state="9").filter(
                                    steprun=steprunlist[0],
                                    verify_items=verifyitem)
                                if len(verifyitemsrunlist) > 0:
                                    runverifyitemid = verifyitemsrunlist[0].id
                                    has_verified = verifyitemsrunlist[
                                        0].has_verified
                                    verifyitemstate = verifyitemsrunlist[
                                        0].state
                            verifyitems.append(
                                {"id": verifyitem.id, "name": verifyitem.name, "runverifyitemid": runverifyitemid,
                                 "has_verified": has_verified,
                                 "verifyitemstate": verifyitemstate})

                    result.append({"id": step.id, "code": step.code, "name": step.name, "approval": step.approval,
                                   "skip": step.skip, "group": group, "time": step.time, "runid": runid,
                                   "starttime": starttime, "endtime": endtime, "operator": operator,
                                   "parameter": parameter, "runresult": runresult, "explain": explain,
                                   "state": state, "scripts": scripts, "verifyitems": verifyitems,
                                   "note": note, "rto": rto,
                                   "children": getchildrensteps(processruns[0], step.sub_process, step.intertype)})
            return HttpResponse(json.dumps(processresult))


def falconstorcontinue(request):
    if request.user.is_authenticated():
        result = {}
        process = request.POST.get('process', '')
        try:
            process = int(process)
        except:
            raise Http404()
        exec_process.delay(process)
        result["res"] = "执行成功。"

        current_process_run = ProcessRun.objects.filter(id=process)
        if current_process_run:
            current_process_run = current_process_run[0]

            all_tasks_ever = current_process_run.processtask_set.filter(
                state="0")
            if all_tasks_ever:
                for task in all_tasks_ever:
                    task.endtime = datetime.datetime.now()
                    task.state = "1"
                    task.save()
        else:
            result["res"] = "流程不存在。"
        return HttpResponse(json.dumps(result))


def get_celery_tasks_info(request):
    if request.user.is_authenticated():
        task_url = "http://127.0.0.1:5555/api/tasks"
        try:
            task_json_info = requests.get(task_url).text
            task_dict_info = json.loads(task_json_info)
            tasks_list = task_dict_info.items()
        except:
            tasks_list = []

        result = []
        if (len(tasks_list) > 0):
            for key, value in tasks_list:
                if value["state"] == "STARTED":
                    received_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(value["received"])) if value[
                        "received"] else ""
                    # succeeded = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(value["succeeded"])) if value[
                    #     "succeeded"] else ""

                    result.append({
                        "uuid": value["uuid"],
                        "args": value["args"][1:-1],
                        "received": received_time,
                        "state": "执行中",
                    })
        # # 根据字典中的值对字典进行排序
        # result = sorted(result, key=itemgetter('received'), reverse=True)
        return JsonResponse({"data": result})


def revoke_current_task(request):
    if request.user.is_authenticated():
        process_run_id = request.POST.get("process_run_id", "")
        abnormal = request.POST.get("abnormal", "")
        task_url = "http://127.0.0.1:5555/api/tasks"

        try:
            task_json_info = requests.get(task_url).text
        except:
            return JsonResponse({"data": "终端未启动flower异步任务监控！"})

        task_dict_info = json.loads(task_json_info)
        task_id = ""

        for key, value in task_dict_info.items():
            if value["state"] == "STARTED":
                task_id = key

        if abnormal == "1":
            stop_url = "http://127.0.0.1:5555/api/task/revoke/{0}?terminate=true".format(
                task_id)
            response = requests.post(stop_url)
            print(response.text)
            task_content = "异步任务被自主关闭。"

            # 终止任务
            if task_id:
                # 修改当前步骤/脚本/流程的状态为ERROR
                set_error_state(request, process_run_id, task_content)

                return JsonResponse({"data": task_content})

            else:
                return JsonResponse({"data": "当前任务不存在"})

        else:
            task_content = "异步任务异常关闭。"

            # 终止任务
            if not task_id:
                # 修改当前步骤/脚本/流程的状态为ERROR
                set_error_state(request, process_run_id, task_content)

                return JsonResponse({"data": task_content})
            else:
                return JsonResponse({"data": "异步任务未出现异常"})


def get_script_log(request):
    if request.user.is_authenticated():
        script_run_id = request.POST.get("scriptRunId", "")
        try:
            script_run_id = int(script_run_id)
        except:
            raise Http404()

        current_script_run = ScriptRun.objects.filter(
            id=script_run_id).select_related("script")
        log_info = ""
        if current_script_run:
            current_script_run = current_script_run[0]
            log_address = current_script_run.script.log_address
            remote_ip = current_script_run.script.ip
            remote_user = current_script_run.script.username
            remote_password = current_script_run.script.password
            script_type = current_script_run.script.type
            if script_type == "SSH":
                remote_platform = "Linux"
                remote_cmd = "cat {0}".format(log_address)
            else:
                remote_platform = "Windows"
                remote_cmd = "type {0}".format(log_address)
            server_obj = ServerByPara(r"{0}".format(remote_cmd), remote_ip, remote_user, remote_password,
                                      remote_platform)
            result = server_obj.run("")
            base_data = result["data"]

            if result["exec_tag"] == "1":
                res = 0
                data = "{0} 导致获取日志信息失败！".format(base_data)
            else:
                res = "1"
                data = base_data
        else:
            res = "0"
            data = "当前脚本不存在！"
        return JsonResponse({
            "res": res,
            "log_info": data,
        })


def processsignsave(request):
    """
    判断是否最后一个签字，如果是,签字后启动程序
    :param request:
    :return:
    """
    if 'task_id' in request.POST:
        result = {}
        id = request.POST.get('task_id', '')
        sign_info = request.POST.get('sign_info', '')

        try:
            id = int(id)
        except:
            raise Http404()
        try:
            process_task = ProcessTask.objects.get(id=id)
            process_task.operator = request.user.username
            process_task.explain = sign_info
            process_task.endtime = datetime.datetime.now()
            process_task.state = "1"
            process_task.save()

            myprocessrun = process_task.processrun

            prosssigns = ProcessTask.objects.filter(
                processrun=myprocessrun, state="0")
            if len(prosssigns) <= 0:
                myprocessrun.state = "RUN"
                myprocessrun.starttime = datetime.datetime.now()
                myprocessrun.save()

                myprocess = myprocessrun.process
                myprocesstask = ProcessTask()
                myprocesstask.processrun = myprocessrun
                myprocesstask.starttime = datetime.datetime.now()
                myprocesstask.type = "INFO"
                myprocesstask.logtype = "START"
                myprocesstask.state = "1"
                myprocesstask.content = "流程已启动。"
                myprocesstask.starttime = datetime.datetime.now()
                myprocesstask.senduser = request.user.username
                myprocesstask.save()

                exec_process.delay(myprocessrun.id)
                result["res"] = "签字成功,同时启动流程。"
                result["data"] = "/processindex/" + str(myprocessrun.id)
            else:
                result["res"] = "签字成功。"
        except:
            result["res"] = "流程启动失败，请于管理员联系。"
        return JsonResponse(result)


def save_task_remark(request):
    if request.user.is_authenticated():
        task_id = request.POST.get("task_id", "")
        sign_info_extra = request.POST.get("sign_info_extra", "")

        if task_id:
            c_process_task = ProcessTask.objects.filter(id=task_id)
            if c_process_task:
                c_process_task = c_process_task[0]
                c_process_task.explain = sign_info_extra
                c_process_task.save()
            return JsonResponse({"result": 1})
        else:
            return JsonResponse({"result": 0})


def reload_task_nums(request):
    if request.user.is_authenticated():
        mygroup = []
        userinfo = request.user.userinfo
        guoups = userinfo.group.all()
        pop = False
        if len(guoups) > 0:
            for curguoup in guoups:
                mygroup.append(str(curguoup.id))
        allprosstasks = ProcessTask.objects.filter(
            Q(receiveauth__in=mygroup) | Q(receiveuser=request.user.username)).filter(state="0").order_by(
            "-starttime").exclude(processrun__state="9").select_related("processrun", "processrun__process",
                                                                        "steprun__step", "steprun")
        total_task_info = {}
        message_task = []
        if len(allprosstasks) > 0:
            for task in allprosstasks:
                send_time = task.starttime
                process_name = task.processrun.process.name
                process_run_reason = task.processrun.run_reason
                task_id = task.id
                processrunid = task.processrun.id

                c_task_step_run = task.steprun
                if c_task_step_run:
                    address = c_task_step_run.step.remark
                    if not address:
                        address = ""
                else:
                    address = ""

                task_nums = len(allprosstasks)
                process_color = task.processrun.process.color
                process_url = task.processrun.process.url + \
                              "/" + str(task.processrun.id)
                time = task.starttime

                # 图标与颜色
                if task.type == "ERROR":
                    current_icon = "fa fa-exclamation-triangle"
                    current_color = "label-danger"
                elif task.type == "SIGN":
                    pop = True
                    current_icon = "fa fa-user"
                    current_color = "label-warning"
                elif task.type == "RUN":
                    current_icon = "fa fa-bell-o"
                    current_color = "label-warning"
                else:
                    pass

                time = custom_time(time)

                message_task.append(
                    {"content": task.content, "time": time, "process_name": process_name, "processrunid": processrunid,
                     "task_color": current_color.strip(), "task_type": task.type, "task_extra": task.content,
                     "task_icon": current_icon, "process_color": process_color.strip(), "process_url": process_url,
                     "pop": pop, "task_id": task_id, "send_time": send_time.strftime("%Y-%m-%d %H:%M:%S"),
                     "process_run_reason": process_run_reason, "group_name": guoups[0].name, "address": address})

        total_task_info["task_nums"] = len(allprosstasks)
        total_task_info["message_task"] = message_task

        return JsonResponse(total_task_info)


def get_current_scriptinfo(request):
    if request.user.is_authenticated():
        current_step_id = request.POST.get('steprunid', '')
        selected_script_id = request.POST.get('scriptid', '')

        if selected_script_id:
            try:
                selected_script_id = int(selected_script_id)
            except:
                selected_script_id = None
        else:
            selected_script_id = None

        scriptrun_objs = ScriptRun.objects.filter(id=selected_script_id)
        script_id = scriptrun_objs[0].script_id if scriptrun_objs else None

        script_objs = Script.objects.filter(id=script_id)
        script_obj = script_objs[0] if script_objs else None

        if script_obj:
            scriptrun_obj = scriptrun_objs[0]
            step_id_from_script = scriptrun_obj.steprun.step_id
            show_button = ""
            if step_id_from_script == current_step_id:
                # 显示button
                show_button = 1
            state_dict = {
                "DONE": "已完成",
                "EDIT": "未执行",
                "RUN": "执行中",
                "ERROR": "执行失败",
                "IGNORE": "忽略",
                "": "",
            }

            starttime = scriptrun_obj.starttime.strftime(
                "%Y-%m-%d %H:%M:%S") if scriptrun_obj.starttime else ""
            endtime = scriptrun_obj.endtime.strftime(
                "%Y-%m-%d %H:%M:%S") if scriptrun_obj.endtime else ""
            script_info = {
                "processrunstate": scriptrun_obj.steprun.processrun.state,
                "code": script_obj.code,
                "ip": script_obj.ip,
                "port": script_obj.port,
                "filename": script_obj.filename,
                "scriptpath": script_obj.scriptpath,
                "state": state_dict["{0}".format(scriptrun_obj.state)],
                "starttime": starttime,
                "endtime": endtime,
                "operator": scriptrun_obj.operator,
                "explain": scriptrun_obj.explain,
                "show_button": show_button,
                "step_id_from_script": step_id_from_script,
                "show_log_btn": "1" if script_obj.log_address else "0",
            }

            return JsonResponse({"data": script_info})


def ignore_current_script(request):
    if request.user.is_authenticated():
        selected_script_id = request.POST.get('scriptid', '')
        scriptruns = ScriptRun.objects.filter(id=selected_script_id)[0]
        scriptruns.state = "IGNORE"
        scriptruns.save()

        # 继续运行
        current_script_run = ScriptRun.objects.filter(id=selected_script_id)
        if current_script_run:
            current_script_run = current_script_run[0]
            current_process_run = current_script_run.steprun.processrun
            current_process_run_id = current_process_run.id
            exec_process.delay(current_process_run_id)

            return JsonResponse({"data": "成功忽略当前脚本！", "result": 1})
        else:
            return JsonResponse({"data": "脚本忽略失败，请联系客服！", "result": 0})


def stop_current_process(request):
    if request.user.is_authenticated():
        process_run_id = request.POST.get('process_run_id', '')
        process_note = request.POST.get('process_note', '')

        if process_run_id:
            process_run_id = int(process_run_id)
        else:
            raise Http404()

        current_process_run = ProcessRun.objects.exclude(
            state="9").filter(id=process_run_id)
        if current_process_run:
            current_process_run = current_process_run[0]

            all_current_step_runs = current_process_run.steprun_set.filter(Q(state="RUN") | Q(state="CONFIRM")).exclude(
                state="9")
            if all_current_step_runs:
                for all_current_step_run in all_current_step_runs:
                    all_current_step_run.state = "EDIT"
                    all_current_step_run.save()
                    all_scripts_from_current_step = all_current_step_run.scriptrun_set.filter(state="RUN").exclude(
                        state="9")
                    if all_scripts_from_current_step:
                        for script in all_scripts_from_current_step:
                            script.state = "EDIT"
                            script.save()

            current_process_run.state = "STOP"
            current_process_run.endtime = datetime.datetime.now()
            current_process_run.note = process_note
            current_process_run.save()

            all_tasks_ever = current_process_run.processtask_set.filter(
                state="0")
            if all_tasks_ever:
                for task in all_tasks_ever:
                    task.endtime = datetime.datetime.now()
                    task.state = "1"
                    task.save()

            myprocesstask = ProcessTask()
            myprocesstask.processrun_id = process_run_id
            myprocesstask.starttime = datetime.datetime.now()
            myprocesstask.senduser = request.user.username
            myprocesstask.type = "INFO"
            myprocesstask.logtype = "STOP"
            myprocesstask.state = "1"
            myprocesstask.content = "流程被终止。"
            myprocesstask.save()
            return JsonResponse({"data": "流程已经被终止"})
        else:
            return JsonResponse({"data": "终止流程异常，请联系客服"})


def verify_items(request):
    if request.user.is_authenticated():
        step_id = request.POST.get("step_id", "")
        current_step_run = StepRun.objects.filter(id=step_id).exclude(state="9").select_related("processrun",
                                                                                                "step").all()
        if current_step_run:
            current_step_run = current_step_run[0]

            # CONFIRM修改成DONE
            current_step_run.state = "DONE"
            current_step_run.endtime = datetime.datetime.now()
            current_step_run.save()

            all_current__tasks = current_step_run.processrun.processtask_set.exclude(
                state="1")
            for task in all_current__tasks:
                task.endtime = datetime.datetime.now()
                task.state = "1"
                task.save()

            # 写入任务
            myprocesstask = ProcessTask()
            myprocesstask.processrun_id = current_step_run.processrun_id
            myprocesstask.starttime = datetime.datetime.now()
            myprocesstask.senduser = current_step_run.processrun.creatuser
            myprocesstask.type = "INFO"
            myprocesstask.logtype = "STEP"
            myprocesstask.state = "1"
            myprocesstask.content = "步骤" + current_step_run.step.name + "完成。"
            myprocesstask.save()

            # 运行流程
            current_process_run_id = current_step_run.processrun_id
            exec_process.delay(current_process_run_id)

            return JsonResponse({"data": "0"})
        else:
            return JsonResponse({"data": "1"})


def show_result(request):
    """
    modify:修改流程明细 step_info_list。
    1.参与系统；
    2.项目组成员；
    3.流程明细；
    :param request:
    :return:
    """
    if request.user.is_authenticated():
        processrun_id = request.POST.get("process_run_id", "")

        show_result_dict = {}

        try:
            processrun_id = int(processrun_id)
        except:
            raise Http404()

        current_processrun = ProcessRun.objects.filter(id=processrun_id)
        if current_processrun:
            current_processrun = current_processrun[0]
        else:
            raise Http404()

        process_name = current_processrun.process.name if current_processrun else ""
        processrun_time = current_processrun.starttime.strftime("%Y-%m-%d")

        # 3.流程明细
        step_info_list = []

        c_process = current_processrun.process
        p_steps = c_process.step_set.order_by("sort").filter(
            state="1", intertype__in=["node", "task", "complex"])

        for num, p_step in enumerate(p_steps):
            # rto, step_name, end_time, operator, start_time, inner_step_list
            p_step_name = ""
            p_start_time = ""
            p_end_time = ""
            p_operator = ""
            p_rto = ""
            inner_step_list = []
            if p_step.intertype == "complex":
                sup_process_id = p_step.sub_process
                sub_process = Process.objects.filter(
                    state="1", id=sup_process_id)
                if sub_process.exists():
                    sub_process = sub_process[0]
                    p_step_name = sub_process.name
                    sub_process_steps = sub_process.step_set.filter(state="1", intertype__in=["node", "task"]).order_by(
                        "drwaid")
                    for sub_process_step in sub_process_steps:
                        # rto, step_name, end_time,start_time, operator
                        step_name = sub_process_step.name

                        rto = ""
                        start_time = ""
                        end_time = ""
                        operator = ""
                        step_run = sub_process_step.steprun_set.filter(
                            processrun=current_processrun)
                        if step_run.exists():
                            step_run = step_run[0]
                            if step_run.step.rto_count_in == "0":
                                start_time = ""
                                end_time = ""
                                rto = ""
                            else:
                                start_time = step_run.starttime.strftime(
                                    "%Y-%m-%d %H:%M:%S") if step_run.starttime else ""
                                end_time = step_run.endtime.strftime(
                                    "%Y-%m-%d %H:%M:%S") if step_run.endtime else ""

                                if step_run.endtime and step_run.starttime:
                                    end_time = step_run.endtime.strftime(
                                        "%Y-%m-%d %H:%M:%S")
                                    start_time = step_run.starttime.strftime(
                                        "%Y-%m-%d %H:%M:%S")
                                    delta_seconds = datetime.datetime.strptime(end_time,
                                                                               '%Y-%m-%d %H:%M:%S') - datetime.datetime.strptime(
                                        start_time, '%Y-%m-%d %H:%M:%S')
                                    hour, minute, second = str(
                                        delta_seconds).split(":")
                                    delta_time = "{0}时{1}分{2}秒".format(
                                        hour, minute, second)
                                    rto = delta_time
                                else:
                                    rto = ""
                            # 操作人员
                            try:
                                users = User.objects.filter(
                                    username=step_run.operator)
                                if users:
                                    operator = users[0].userinfo.fullname
                                else:
                                    operator = ""
                            except:
                                operator = ""

                        inner_step_list.append({
                            "rto": rto,
                            "step_name": step_name,
                            "end_time": end_time,
                            "start_time": start_time,
                            "operator": operator,
                        })
            else:
                p_step_name = p_step.name

                p_rto = ""
                p_start_time = ""
                p_end_time = ""
                p_operator = ""
                step_run = p_step.steprun_set.filter(
                    processrun=current_processrun)
                if step_run.exists():
                    step_run = step_run[0]
                    if step_run.step.rto_count_in == "0":
                        p_start_time = ""
                        p_end_time = ""
                        p_rto = ""
                    else:
                        p_start_time = step_run.starttime.strftime(
                            "%Y-%m-%d %H:%M:%S") if step_run.starttime else ""
                        p_end_time = step_run.endtime.strftime(
                            "%Y-%m-%d %H:%M:%S") if step_run.endtime else ""

                        if step_run.endtime and step_run.starttime:
                            p_end_time = step_run.endtime.strftime(
                                "%Y-%m-%d %H:%M:%S")
                            p_start_time = step_run.starttime.strftime(
                                "%Y-%m-%d %H:%M:%S")
                            delta_seconds = datetime.datetime.strptime(p_end_time,
                                                                       '%Y-%m-%d %H:%M:%S') - datetime.datetime.strptime(
                                p_start_time, '%Y-%m-%d %H:%M:%S')
                            hour, minute, second = str(
                                delta_seconds).split(":")
                            delta_time = "{0}时{1}分{2}秒".format(
                                hour, minute, second)
                            p_rto = delta_time
                        else:
                            p_rto = ""
                    # 操作人员
                    try:
                        users = User.objects.filter(username=step_run.operator)
                        if users:
                            p_operator = users[0].userinfo.fullname
                        else:
                            p_operator = ""
                    except:
                        p_operator = ""

            step_info_list.append({
                "rto": p_rto,
                "step_name": p_step_name,
                "operator": p_operator,
                "start_time": p_start_time,
                "end_time": p_end_time,
                "inner_step_list": inner_step_list
            })

        show_result_dict["step_info_list"] = step_info_list
        # 3.项目组成员
        all_groups = Group.objects.exclude(state="9")
        total_list = []
        if all_groups:
            for group in all_groups:
                all_group_dict = {}
                current_group_users = group.userinfo_set.exclude(
                    state="9", pnode=None).filter(type="user")
                if current_group_users:
                    all_group_dict["group"] = group.name

                    current_users_and_departments = []
                    for user in current_group_users:
                        inner_dict = {}
                        inner_dict["fullname"] = user.fullname
                        inner_dict[
                            "depart_name"] = user.pnode.fullname if user.pnode else ""
                        current_users_and_departments.append(inner_dict)
                    all_group_dict[
                        "current_users_and_departments"] = current_users_and_departments
                    total_list.append(all_group_dict)
        show_result_dict["total_list"] = total_list

        # 1.参与系统
        show_result_dict["process_name"] = process_name
        show_result_dict["processrun_time"] = processrun_time

        # 项目起始时间，结束时间
        show_result_dict["start_time"] = current_processrun.starttime.strftime(
            "%Y-%m-%d %H:%M:%S") if current_processrun.starttime else ""
        show_result_dict["end_time"] = current_processrun.endtime.strftime(
            "%Y-%m-%d %H:%M:%S") if current_processrun.endtime else ""

        # 总环节RTO
        rto = current_processrun.rto
        m, s = divmod(rto, 60)
        h, m = divmod(m, 60)
        show_result_dict["rto"] = "%d时%02d分%02d秒" % (h, m, s)

        return JsonResponse(show_result_dict)


def reject_invited(request):
    if request.user.is_authenticated():
        plan_process_run_id = request.POST.get("plan_process_run_id", "")
        rejected_process_runs = ProcessRun.objects.filter(
            id=plan_process_run_id)
        if rejected_process_runs:
            rejected_process_run = rejected_process_runs[0]
            rejected_process_run.state = "REJECT"
            rejected_process_run.save()

            # 生成取消任务信息
            myprocesstask = ProcessTask()
            myprocesstask.processrun_id = rejected_process_run.id
            myprocesstask.starttime = datetime.datetime.now()
            myprocesstask.senduser = request.user.username
            myprocesstask.type = "INFO"
            myprocesstask.logtype = "REJECT"
            myprocesstask.state = "1"
            myprocesstask.content = "取消演练计划。"
            myprocesstask.save()

            result = "取消演练计划成功！"
        else:
            result = "计划流程不存在，取消失败！"
        return JsonResponse({"res": result})


def delete_current_process_run(request):
    if request.user.is_authenticated():
        processrun_id = request.POST.get("processrun_id", "")

        try:
            processrun_id = int(processrun_id)
        except:
            raise Http404()

        current_process_run = ProcessRun.objects.filter(id=processrun_id)
        if current_process_run:
            current_process_run = current_process_run[0]
            current_process_run.state = "9"
            current_process_run.save()
            return HttpResponse(1)
        else:
            return HttpResponse(0)


def custom_pdf_report(request):
    """
    pip3 install pdfkit
    wkhtmltopdf安装文件已经在项目中static/process
    """
    if request.user.is_authenticated():
        processrun_id = request.GET.get("processrunid", "")
        process_id = request.GET.get("processid", "")

        # 构造数据
        # 1.获取当前流程对象
        process_run_objs = ProcessRun.objects.filter(id=processrun_id)
        if process_run_objs:
            process_run_obj = process_run_objs[0]
        else:
            raise Http404()

        # 2.报表封页文字
        title_xml = "自动化切换流程"
        abstract_xml = "切换报告"

        # 3.章节名称
        ele_xml01 = "一、切换概述"
        ele_xml02 = "二、步骤详情"

        # 4.构造第一章数据: first_el_dict
        # 切换概述节点下内容,有序字典中存放
        first_el_dict = {}

        start_time = process_run_obj.starttime
        end_time = process_run_obj.endtime
        create_user = process_run_obj.creatuser
        users = User.objects.filter(username=create_user)
        if users:
            create_user = users[0].userinfo.fullname
        else:
            create_user = ""
        run_reason = process_run_obj.run_reason

        first_el_dict["start_time"] = r"{0}".format(
            start_time.strftime("%Y-%m-%d %H:%M:%S") if start_time else "")
        first_el_dict["end_time"] = r"{0}".format(
            end_time.strftime("%Y-%m-%d %H:%M:%S") if end_time else "")

        # RTO
        # 总环节RTO
        step_rto = process_run_obj.rto

        m, s = divmod(step_rto, 60)
        h, m = divmod(m, 60)
        first_el_dict["rto"] = "%d时%02d分%02d秒" % (h, m, s)

        first_el_dict["create_user"] = r"{0}".format(create_user)

        task_sign_obj = ProcessTask.objects.filter(processrun_id=processrun_id).exclude(state="9").filter(
            type="SIGN")

        if task_sign_obj:
            receiveusers = ""
            for task in task_sign_obj:
                receiveuser = task.receiveuser

                users = User.objects.filter(username=receiveuser)
                if users:
                    receiveuser = users[0].userinfo.fullname

                if receiveuser:
                    receiveusers += receiveuser + "、"

            first_el_dict["receiveuser"] = r"{0}".format(receiveusers[:-1])

        all_steprun_objs = StepRun.objects.filter(processrun_id=processrun_id)
        operators = ""
        for steprun_obj in all_steprun_objs:
            if steprun_obj.operator:
                if steprun_obj.operator not in operators:
                    users = User.objects.filter(username=steprun_obj.operator)
                    if users:
                        operator = users[0].userinfo.fullname
                        if operator:
                            if operator not in operators:
                                operators += operator + "、"

        first_el_dict["operator"] = r"{0}".format(operators[:-1])
        first_el_dict["run_reason"] = r"{0}".format(run_reason)

        step_info_list = []

        c_process = process_run_obj.process
        pnode_steplist = c_process.step_set.order_by("sort").filter(state="1",
                                                                    intertype__in=["node", "task", "complex"])

        for num, pstep in enumerate(pnode_steplist):
            second_el_dict = {}
            inner_step_list = []
            # 当前步骤下脚本
            state_dict = {
                "DONE": "已完成",
                "EDIT": "未执行",
                "RUN": "执行中",
                "ERROR": "执行失败",
                "IGNORE": "忽略",
                "": "",
            }
            if pstep.intertype == "complex":
                sup_process_id = pstep.sub_process
                sub_process = Process.objects.filter(
                    state="1", id=sup_process_id)

                # 子流程下步骤信息
                if sub_process.exists():
                    sub_process = sub_process[0]

                    p_step_name = sub_process.name
                    step_name = "{0}.{1}".format(num + 1, p_step_name)
                    second_el_dict["step_name"] = step_name

                    sub_process_steps = sub_process.step_set.filter(state="1", intertype__in=["node", "task"]).order_by(
                        "drwaid")
                    for num, step in enumerate(sub_process_steps):
                        inner_second_el_dict = {}
                        step_name = "{0}){1}".format(num + 1, step.name)
                        inner_second_el_dict["step_name"] = step_name
                        steprun_obj = StepRun.objects.exclude(state="9").filter(processrun_id=processrun_id).filter(
                            step=step)
                        if steprun_obj:
                            steprun_obj = steprun_obj[0]
                            if steprun_obj.step.rto_count_in == "0":
                                inner_second_el_dict["start_time"] = ""
                                inner_second_el_dict["end_time"] = ""
                                inner_second_el_dict["rto"] = ""
                            else:
                                inner_second_el_dict["start_time"] = steprun_obj.starttime.strftime(
                                    "%Y-%m-%d %H:%M:%S") if \
                                    steprun_obj.starttime else ""
                                inner_second_el_dict["end_time"] = steprun_obj.endtime.strftime(
                                    "%Y-%m-%d %H:%M:%S") if steprun_obj.endtime else ""

                                if steprun_obj.endtime and steprun_obj.starttime:
                                    end_time = steprun_obj.endtime.strftime(
                                        "%Y-%m-%d %H:%M:%S")
                                    start_time = steprun_obj.starttime.strftime(
                                        "%Y-%m-%d %H:%M:%S")
                                    delta_seconds = datetime.datetime.strptime(end_time,
                                                                               '%Y-%m-%d %H:%M:%S') - datetime.datetime.strptime(
                                        start_time, '%Y-%m-%d %H:%M:%S')
                                    hour, minute, second = str(
                                        delta_seconds).split(":")

                                    delta_time = "{0}时{1}分{2}秒".format(
                                        hour, minute, second)

                                    inner_second_el_dict["rto"] = delta_time
                                else:
                                    inner_second_el_dict["rto"] = ""

                            # 步骤负责人
                            users = User.objects.filter(
                                username=steprun_obj.operator)
                            if users:
                                operator = users[0].userinfo.fullname
                                inner_second_el_dict["operator"] = operator
                            else:
                                inner_second_el_dict["operator"] = ""

                            # 当前步骤下脚本
                            current_scripts = Script.objects.exclude(
                                state="9").filter(step_id=step.id)

                            script_list_inner = []
                            if current_scripts:
                                for snum, current_script in enumerate(current_scripts):
                                    script_el_dict_inner = DictIndex()
                                    # title
                                    script_name = "{0}.{1}".format(
                                        "i" * (snum + 1), current_script.name)
                                    script_el_dict_inner[
                                        "script_name"] = script_name

                                    # content
                                    steprun_id = steprun_obj.id
                                    script_id = current_script.id
                                    current_scriptrun_obj = ScriptRun.objects.filter(steprun_id=steprun_id,
                                                                                     script_id=script_id)
                                    if current_scriptrun_obj:
                                        current_scriptrun_obj = current_scriptrun_obj[
                                            0]
                                        script_el_dict_inner["start_time"] = current_scriptrun_obj.starttime.strftime(
                                            "%Y-%m-%d %H:%M:%S") if current_scriptrun_obj.starttime else ""
                                        script_el_dict_inner["end_time"] = current_scriptrun_obj.endtime.strftime(
                                            "%Y-%m-%d %H:%M:%S") if current_scriptrun_obj.endtime else ""

                                        if current_scriptrun_obj.endtime and current_scriptrun_obj.starttime:
                                            end_time = current_scriptrun_obj.endtime.strftime(
                                                "%Y-%m-%d %H:%M:%S")
                                            start_time = current_scriptrun_obj.starttime.strftime(
                                                "%Y-%m-%d %H:%M:%S")
                                            delta_seconds = datetime.datetime.strptime(end_time,
                                                                                       '%Y-%m-%d %H:%M:%S') - datetime.datetime.strptime(
                                                start_time, '%Y-%m-%d %H:%M:%S')
                                            hour, minute, second = str(
                                                delta_seconds).split(":")

                                            delta_time = "{0}时{1}分{2}秒".format(
                                                hour, minute, second)

                                            script_el_dict_inner[
                                                "rto"] = delta_time
                                        else:
                                            script_el_dict_inner["rto"] = ""

                                        state = current_scriptrun_obj.state
                                        if state in state_dict.keys():
                                            script_el_dict_inner[
                                                "state"] = state_dict[state]
                                        else:
                                            script_el_dict_inner["state"] = ""

                                        script_el_dict_inner[
                                            "explain"] = current_scriptrun_obj.explain
                                    else:
                                        pass
                                    script_list_inner.append(
                                        script_el_dict_inner)
                            inner_second_el_dict[
                                "script_list_inner"] = script_list_inner
                        inner_step_list.append(inner_second_el_dict)
            else:
                step_name = "{0}.{1}".format(num + 1, pstep.name)
                second_el_dict["step_name"] = step_name
                pnode_steprun = pstep.steprun_set.filter(
                    processrun=process_run_obj)
                if pnode_steprun:
                    pnode_steprun = pnode_steprun[0]
                    if pnode_steprun.step.rto_count_in == "0":
                        second_el_dict["start_time"] = ""
                        second_el_dict["end_time"] = ""
                        second_el_dict["rto"] = ""
                    else:
                        second_el_dict["start_time"] = pnode_steprun.starttime.strftime("%Y-%m-%d %H:%M:%S") if \
                            pnode_steprun.starttime else ""
                        second_el_dict["end_time"] = pnode_steprun.endtime.strftime(
                            "%Y-%m-%d %H:%M:%S") if pnode_steprun.endtime else ""

                        if pnode_steprun.endtime and pnode_steprun.starttime:
                            end_time = pnode_steprun.endtime.strftime(
                                "%Y-%m-%d %H:%M:%S")
                            start_time = pnode_steprun.starttime.strftime(
                                "%Y-%m-%d %H:%M:%S")
                            delta_seconds = datetime.datetime.strptime(end_time,
                                                                       '%Y-%m-%d %H:%M:%S') - datetime.datetime.strptime(
                                start_time, '%Y-%m-%d %H:%M:%S')
                            hour, minute, second = str(
                                delta_seconds).split(":")

                            delta_time = "{0}时{1}分{2}秒".format(
                                hour, minute, second)

                            second_el_dict["rto"] = delta_time
                        else:
                            second_el_dict["rto"] = ""

                # 步骤负责人
                try:
                    users = User.objects.filter(
                        username=pnode_steprun.operator)
                except:
                    if users:
                        operator = users[0].userinfo.fullname
                        second_el_dict["operator"] = operator
                    else:
                        second_el_dict["operator"] = ""

                current_scripts = Script.objects.exclude(
                    state="9").filter(step_id=pstep.id)
                script_list_wrapper = []
                if current_scripts:
                    for snum, current_script in enumerate(current_scripts):
                        script_el_dict = DictIndex()
                        # title
                        script_name = "{0}.{1}".format(
                            "i" * (snum + 1), current_script.name)
                        script_el_dict["script_name"] = script_name
                        # content
                        steprun_id = pnode_steprun.id if pnode_steprun else None
                        script_id = current_script.id
                        current_scriptrun_obj = ScriptRun.objects.filter(
                            steprun_id=steprun_id, script_id=script_id)
                        if current_scriptrun_obj:
                            current_scriptrun_obj = current_scriptrun_obj[0]
                            script_el_dict["start_time"] = current_scriptrun_obj.starttime.strftime(
                                "%Y-%m-%d %H:%M:%S") if current_scriptrun_obj.starttime else ""
                            script_el_dict["end_time"] = current_scriptrun_obj.endtime.strftime(
                                "%Y-%m-%d %H:%M:%S") if current_scriptrun_obj.endtime else ""

                            if current_scriptrun_obj.endtime and current_scriptrun_obj.starttime:
                                end_time = current_scriptrun_obj.endtime.strftime(
                                    "%Y-%m-%d %H:%M:%S")
                                start_time = current_scriptrun_obj.starttime.strftime(
                                    "%Y-%m-%d %H:%M:%S")
                                delta_seconds = datetime.datetime.strptime(end_time,
                                                                           '%Y-%m-%d %H:%M:%S') - datetime.datetime.strptime(
                                    start_time, '%Y-%m-%d %H:%M:%S')
                                hour, minute, second = str(
                                    delta_seconds).split(":")

                                delta_time = "{0}时{1}分{2}秒".format(
                                    hour, minute, second)

                                script_el_dict["rto"] = delta_time
                            else:
                                script_el_dict["rto"] = ""

                            state = current_scriptrun_obj.state
                            if state in state_dict.keys():
                                script_el_dict["state"] = state_dict[state]
                            else:
                                script_el_dict["state"] = ""
                            script_el_dict[
                                "explain"] = current_scriptrun_obj.explain

                        script_list_wrapper.append(script_el_dict)
                    second_el_dict["script_list_wrapper"] = script_list_wrapper

            second_el_dict['inner_step_list'] = inner_step_list
            step_info_list.append(second_el_dict)

        # return render(request, "pdf.html", locals())
        t = TemplateResponse(request, 'pdf.html',
                             {"step_info_list": step_info_list, "first_el_dict": first_el_dict, "ele_xml01": ele_xml01,
                              "ele_xml02": ele_xml02, "title_xml": title_xml, "abstract_xml": abstract_xml})
        t.render()
        current_path = os.getcwd()

        if sys.platform.startswith("win"):
            # 指定wkhtmltopdf运行程序路径
            wkhtmltopdf_path = current_path + os.sep + "faconstor" + os.sep + "static" + os.sep + \
                               "process" + os.sep + "wkhtmltopdf" + os.sep + "bin" + os.sep + "wkhtmltopdf.exe"
            config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
        else:
            config = None

        options = {
            'page-size': 'A3',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8",
            'no-outline': None
        }
        css_path = current_path + os.sep + "faconstor" + os.sep + "static" + \
                   os.sep + "new" + os.sep + "css" + os.sep + "bootstrap.css"
        css = [r"{0}".format(css_path)]

        pdfkit.from_string(t.content.decode(encoding="utf-8"), r"falconstor.pdf", configuration=config,
                           options=options, css=css)

        the_file_name = "falconstor.pdf"
        response = StreamingHttpResponse(file_iterator(the_file_name))
        response['Content-Type'] = 'application/octet-stream; charset=unicode'
        response['Content-Disposition'] = 'attachment;filename="{0}"'.format(
            the_file_name)
        return response


def falconstorsearch(request, funid):
    if request.user.is_authenticated():
        nowtime = datetime.datetime.now()
        endtime = nowtime.strftime("%Y-%m-%d")
        starttime = (nowtime - datetime.timedelta(days=30)
                     ).strftime("%Y-%m-%d")
        all_processes = Process.objects.exclude(
            state="9").filter(type="falconstor")
        processname_list = []
        for process in all_processes:
            processname_list.append(process.name)

        state_dict = {
            "DONE": "已完成",
            "EDIT": "未执行",
            "RUN": "执行中",
            "ERROR": "执行失败",
            "IGNORE": "忽略",
            "STOP": "终止",
            "PLAN": "计划",
            "SIGN": "签到",
        }
        return render(request, "falconstorsearch.html",
                      {'username': request.user.userinfo.fullname, "starttime": starttime, "endtime": endtime,
                       "processname_list": processname_list, "state_dict": state_dict,
                       "pagefuns": getpagefuns(funid, request=request)})
    else:
        return HttpResponseRedirect("/login")


def falconstorsearchdata(request):
    """
    :param request: starttime, endtime, runperson, runstate
    :return: starttime,endtime,createuser,state,process_id,processrun_id,runreason
    """
    if request.user.is_authenticated():
        result = []
        processname = request.GET.get('processname', '')
        runperson = request.GET.get('runperson', '')
        runstate = request.GET.get('runstate', '')
        startdate = request.GET.get('startdate', '')
        enddate = request.GET.get('enddate', '')
        start_time = datetime.datetime.strptime(
            startdate, '%Y-%m-%d').strftime('%Y-%m-%d %H:%M:%S')
        end_time = (datetime.datetime.strptime(enddate, '%Y-%m-%d') + datetime.timedelta(days=1) - datetime.timedelta(
            seconds=1)).strftime('%Y-%m-%d %H:%M:%S')

        cursor = connection.cursor()

        exec_sql = """
        select r.starttime, r.endtime, r.creatuser, r.state, r.process_id, r.id, r.run_reason, p.name, p.url from faconstor_processrun as r 
        left join faconstor_process as p on p.id = r.process_id where r.state != '9' and r.state!='REJECT' and r.starttime between '{0}' and '{1}' order by r.starttime desc;
        """.format(start_time, end_time)

        if runperson:
            user_info = UserInfo.objects.filter(fullname=runperson)
            if user_info:
                user_info = user_info[0]
                runperson = user_info.user.username
            else:
                runperson = ""

            if processname != "" and runstate != "":
                exec_sql = """
                select r.starttime, r.endtime, r.creatuser, r.state, r.process_id, r.id, r.run_reason, p.name, p.url from faconstor_processrun as r 
                left join faconstor_process as p on p.id = r.process_id where r.state != '9' and r.state!='REJECT' and p.name='{0}' and r.state='{1}' and r.creatuser='{2}' and r.starttime between '{3}' and '{4}'  order by r.starttime desc;
                """.format(processname, runstate, runperson, start_time, end_time)

            if processname == "" and runstate != "":
                exec_sql = """
                select r.starttime, r.endtime, r.creatuser, r.state, r.process_id, r.id, r.run_reason, p.name, p.url from faconstor_processrun as r 
                left join faconstor_process as p on p.id = r.process_id where r.state != '9' and r.state!='REJECT' and r.state='{0}' and r.creatuser='{1}' and r.starttime between '{2}' and '{3}'  order by r.starttime desc;
                """.format(runstate, runperson, start_time, end_time)

            if processname != "" and runstate == "":
                exec_sql = """
                select r.starttime, r.endtime, r.creatuser, r.state, r.process_id, r.id, r.run_reason, p.name, p.url from faconstor_processrun as r 
                left join faconstor_process as p on p.id = r.process_id where r.state != '9' and r.state!='REJECT' and p.name='{0}' and r.creatuser='{1}' and r.starttime between '{2}' and '{3}'  order by r.starttime desc;
                """.format(processname, runperson, start_time, end_time)
            if processname == "" and runstate == "":
                exec_sql = """
                select r.starttime, r.endtime, r.creatuser, r.state, r.process_id, r.id, r.run_reason, p.name, p.url from faconstor_processrun as r 
                left join faconstor_process as p on p.id = r.process_id where r.state != '9' and r.state!='REJECT' and r.creatuser='{0}' and r.starttime between '{1}' and '{2}'  order by r.starttime desc;
                """.format(runperson, start_time, end_time)

        else:
            if processname != "" and runstate != "":
                exec_sql = """
                select r.starttime, r.endtime, r.creatuser, r.state, r.process_id, r.id, r.run_reason, p.name, p.url from faconstor_processrun as r 
                left join faconstor_process as p on p.id = r.process_id where r.state != '9' and r.state!='REJECT' and p.name='{0}' and r.state='{1}' and r.starttime between '{2}' and '{3}'  order by r.starttime desc;
                """.format(processname, runstate, start_time, end_time)

            if processname == "" and runstate != "":
                exec_sql = """
                select r.starttime, r.endtime, r.creatuser, r.state, r.process_id, r.id, r.run_reason, p.name, p.url from faconstor_processrun as r 
                left join faconstor_process as p on p.id = r.process_id where r.state != '9' and r.state!='REJECT' and r.state='{0}' and r.starttime between '{1}' and '{2}'  order by r.starttime desc;
                """.format(runstate, start_time, end_time)

            if processname != "" and runstate == "":
                exec_sql = """
                select r.starttime, r.endtime, r.creatuser, r.state, r.process_id, r.id, r.run_reason, p.name, p.url from faconstor_processrun as r 
                left join faconstor_process as p on p.id = r.process_id where r.state != '9' and r.state!='REJECT' and p.name='{0}' and r.starttime between '{1}' and '{2}'  order by r.starttime desc;
                """.format(processname, start_time, end_time)

        state_dict = {
            "DONE": "已完成",
            "EDIT": "未执行",
            "RUN": "执行中",
            "ERROR": "执行失败",
            "IGNORE": "忽略",
            "STOP": "终止",
            "PLAN": "计划",
            "REJECT": "取消",
            "SIGN": "签到",
            "": "",
        }
        cursor.execute(exec_sql)
        rows = cursor.fetchall()

        for processrun_obj in rows:
            create_users = processrun_obj[2] if processrun_obj[2] else ""
            create_user_objs = User.objects.filter(username=create_users)
            create_user_fullname = create_user_objs[
                0].userinfo.fullname if create_user_objs else ""

            result.append({
                "starttime": processrun_obj[0].strftime('%Y-%m-%d %H:%M:%S') if processrun_obj[0] else "",
                "endtime": processrun_obj[1].strftime('%Y-%m-%d %H:%M:%S') if processrun_obj[1] else "",
                "createuser": create_user_fullname,
                "state": state_dict["{0}".format(processrun_obj[3])] if processrun_obj[3] else "",
                "process_id": processrun_obj[4] if processrun_obj[4] else "",
                "processrun_id": processrun_obj[5] if processrun_obj[5] else "",
                "run_reason": processrun_obj[6][:20] if processrun_obj[6] else "",
                "process_name": processrun_obj[7] if processrun_obj[7] else "",
                "process_url": processrun_obj[8] if processrun_obj[8] else ""
            })
        return HttpResponse(json.dumps({"data": result}))


def tasksearch(request, funid):
    if request.user.is_authenticated():
        nowtime = datetime.datetime.now()
        endtime = nowtime.strftime("%Y-%m-%d")
        starttime = (nowtime - datetime.timedelta(days=30)
                     ).strftime("%Y-%m-%d")
        all_processes = Process.objects.exclude(
            state="9").filter(type="falconstor")
        processname_list = []
        for process in all_processes:
            processname_list.append(process.name)

        return render(request, "tasksearch.html",
                      {'username': request.user.userinfo.fullname, "starttime": starttime, "endtime": endtime,
                       "processname_list": processname_list, "pagefuns": getpagefuns(funid, request=request)})
    else:
        return HttpResponseRedirect("/login")


def tasksearchdata(request):
    if request.user.is_authenticated():
        result = []
        task_type = request.GET.get('task_type', '')
        has_finished = request.GET.get('has_finished', '')
        startdate = request.GET.get('startdate', '')
        enddate = request.GET.get('enddate', '')
        start_time = datetime.datetime.strptime(
            startdate, '%Y-%m-%d').strftime('%Y-%m-%d %H:%M:%S')
        end_time = (datetime.datetime.strptime(enddate, '%Y-%m-%d') + datetime.timedelta(days=1) - datetime.timedelta(
            seconds=1)).strftime('%Y-%m-%d %H:%M:%S')

        cursor = connection.cursor()
        exec_sql = """
        select t.id, t.content, t.starttime, t.endtime, t.type, t.processrun_id, p.name, p.url, t.state from faconstor_processtask as t 
        left join faconstor_processrun as r on t.processrun_id = r.id left join faconstor_process as p on p.id = r.process_id where t.type!='INFO' and r.state!='9' and t.starttime between '{0}' and '{1}' order by t.starttime desc;
        """.format(start_time, end_time)

        if task_type != "" and has_finished != "":
            exec_sql = """
            select t.id, t.content, t.starttime, t.endtime, t.type, t.processrun_id, p.name, p.url, t.state from faconstor_processtask as t 
            left join faconstor_processrun as r on t.processrun_id = r.id left join faconstor_process as p on p.id = r.process_id where t.type='{0}' and r.state!='9' and t.state='{1}' and t.starttime between '{2}' and '{3}' order by t.starttime desc;
            """.format(task_type, has_finished, start_time, end_time)

        if task_type == "" and has_finished != "":
            exec_sql = """
            select t.id, t.content, t.starttime, t.endtime, t.type, t.processrun_id, p.name, p.url, t.state from faconstor_processtask as t 
            left join faconstor_processrun as r on t.processrun_id = r.id left join faconstor_process as p on p.id = r.process_id where  t.type!='INFO' and r.state!='9' and t.state='{0}' and t.starttime between '{1}' and '{2}' order by t.starttime desc;
            """.format(has_finished, start_time, end_time)

        if task_type != "" and has_finished == "":
            exec_sql = """
            select t.id, t.content, t.starttime, t.endtime, t.type, t.processrun_id, p.name, p.url, t.state from faconstor_processtask as t 
            left join faconstor_processrun as r on t.processrun_id = r.id left join faconstor_process as p on p.id = r.process_id where t.type='{0}' and r.state!='9' and t.starttime between '{1}' and '{2}' order by t.starttime desc;
            """.format(task_type, start_time, end_time)

        cursor.execute(exec_sql)
        rows = cursor.fetchall()
        type_dict = {
            "SIGN": "签到",
            "RUN": "操作",
            "ERROR": "错误",
            "": "",
        }

        has_finished_dict = {
            "1": "完成",
            "0": "未完成"
        }
        for task in rows:
            result.append({
                "task_id": task[0],
                "task_content": task[1],
                "starttime": task[2].strftime('%Y-%m-%d %H:%M:%S') if task[2] else "",
                "endtime": task[3].strftime('%Y-%m-%d %H:%M:%S') if task[3] else "",
                "type": type_dict["{0}".format(task[4])] if task[4] in type_dict.keys() else "",
                "processrun_id": task[5] if task[5] else "",
                "process_name": task[6] if task[6] else "",
                "process_url": task[7] if task[7] else "",
                "has_finished": has_finished_dict[
                    "{0}".format(task[8])] if task[8] in has_finished_dict.keys() else "",
            })
        return JsonResponse({"data": result})


def downloadlist(request, funid):
    if request.user.is_authenticated():
        errors = []
        if request.method == 'POST':
            file_remark = request.POST.get("file_remark", "")
            my_file = request.FILES.get("myfile", None)
            if not my_file:
                errors.append("请选择要导入的文件。")
            else:
                if if_contains_sign(my_file.name):
                    errors.append(r"""请注意文件命名格式，'\/"*?<>'符号文件不允许上传。""")
                else:
                    myfilepath = settings.BASE_DIR + os.sep + "faconstor" + os.sep + \
                                 "upload" + os.sep + "knowledgefiles" + os.sep + my_file.name

                    c_exist_model = KnowledgeFileDownload.objects.filter(
                        file_name=my_file.name).exclude(state="9")

                    if os.path.exists(myfilepath) or c_exist_model.exists():
                        errors.append("该文件已存在,请勿重复上传。")
                    else:
                        with open(myfilepath, 'wb+') as f:
                            for chunk in my_file.chunks():  # 分块写入文件
                                f.write(chunk)

                        # 存入字段：备注，上传时间，上传人
                        c_file = KnowledgeFileDownload()
                        c_file.file_name = my_file.name
                        c_file.person = request.user.userinfo.fullname
                        c_file.remark = file_remark
                        c_file.upload_time = datetime.datetime.now()
                        c_file.save()

                        errors.append("导入成功。")
        return render(request, "downloadlist.html",
                      {'username': request.user.userinfo.fullname, "errors": errors,
                       "pagefuns": getpagefuns(funid, request=request)})
    else:
        return HttpResponseRedirect("/login")


def download_list_data(request):
    if request.user.is_authenticated():
        result = []
        c_files = KnowledgeFileDownload.objects.exclude(state="9")
        if c_files.exists():
            for file in c_files:
                result.append({
                    "id": file.id,
                    "name": file.person,
                    "up_time": "{0:%Y-%m-%d %H:%M:%S}".format(file.upload_time),
                    "remark": file.remark,
                    "file_name": file.file_name,
                })

        return JsonResponse({
            "data": result
        })


def knowledge_file_del(request):
    if request.user.is_authenticated():
        file_id = request.POST.get("id", "")
        assert int(file_id), "网页异常"

        c_file = KnowledgeFileDownload.objects.filter(id=file_id)
        if c_file.exists():
            c_file = c_file[0]
            c_file.delete()
            c_file_name = c_file.file_name
            the_file_name = settings.BASE_DIR + os.sep + "faconstor" + os.sep + \
                            "upload" + os.sep + "knowledgefiles" + os.sep + c_file_name
            if os.path.exists(the_file_name):
                os.remove(the_file_name)
            result = "删除成功。"
        else:
            result = "文件不存在，删除失败,请于管理员联系。"

        return JsonResponse({
            "data": result
        })


def download(request):
    if request.user.is_authenticated():
        file_id = request.GET.get("file_id", "")
        assert int(file_id), "网页异常"
        c_file = KnowledgeFileDownload.objects.filter(id=file_id)
        if c_file.exists():
            c_file = c_file[0]
            c_file_name = c_file.file_name
        else:
            raise Http404()
        try:
            the_file_name = settings.BASE_DIR + os.sep + "faconstor" + os.sep + \
                            "upload" + os.sep + "knowledgefiles" + os.sep + c_file_name
            response = StreamingHttpResponse(file_iterator(the_file_name))
            response['Content-Type'] = 'application/octet-stream; charset=unicode'
            response['Content-Disposition'] = 'attachment;filename="{0}"'.format(
                escape_uri_path(c_file_name))  # escape_uri_path()解决中文名文件
            return response
        except:
            return HttpResponseRedirect("/downloadlist")
    else:
        return HttpResponseRedirect("/login")


def save_invitation(request):
    if request.user.is_authenticated():
        result = {}
        process_id = request.POST.get("process_id", "")
        start_time = request.POST.get("start_time", "")
        purpose = request.POST.get("purpose", "")
        end_time = request.POST.get("end_time", "")

        # 准备流程PLAN
        try:
            process_id = int(process_id)
        except:
            raise Http404()

        if start_time:
            if end_time:
                process = Process.objects.filter(id=process_id).exclude(
                    state="9").filter(type="falconstor")
                if (len(process) <= 0):
                    result["res"] = '流程计划失败，该流程不存在。'
                else:

                    planning_process = ProcessRun.objects.filter(
                        process=process[0], state="PLAN")
                    if (len(planning_process) > 0):
                        result["res"] = '流程计划失败，已经存在计划流程，务必先完成该计划流程。'
                    else:
                        curprocessrun = ProcessRun.objects.filter(
                            process=process[0], state__in=["RUN", "ERROR"])
                        if (len(curprocessrun) > 0):
                            result["res"] = '流程计划失败，有流程正在进行中，请勿重复启动。'
                        else:
                            myprocessrun = ProcessRun()
                            myprocessrun.process = process[0]
                            myprocessrun.state = "PLAN"
                            myprocessrun.starttime = datetime.datetime.now()
                            myprocessrun.save()
                            current_process_run_id = myprocessrun.id

                            # 1.子流程下所有步骤都要生成对应的StepRun.
                            mysteps = custom_all_steps(process[0])

                            if (len(mysteps) <= 0):
                                result["res"] = '流程启动失败，没有找到可用步骤。'
                            else:
                                for step in mysteps:
                                    mysteprun = StepRun()
                                    mysteprun.step = step
                                    mysteprun.processrun = myprocessrun
                                    mysteprun.state = "EDIT"
                                    mysteprun.save()

                                    myscript = step.script_set.exclude(
                                        state="9")
                                    for script in myscript:
                                        myscriptrun = ScriptRun()
                                        myscriptrun.script = script
                                        myscriptrun.steprun = mysteprun
                                        myscriptrun.state = "EDIT"
                                        myscriptrun.save()

                                    myverifyitems = step.verifyitems_set.exclude(
                                        state="9")
                                    for verifyitems in myverifyitems:
                                        myverifyitemsrun = VerifyItemsRun()
                                        myverifyitemsrun.verify_items = verifyitems
                                        myverifyitemsrun.steprun = mysteprun
                                        myverifyitemsrun.save()

                            # 保存邀请函
                            current_invitation = Invitation()
                            current_invitation.process_run_id = current_process_run_id
                            current_invitation.start_time = start_time
                            current_invitation.end_time = end_time
                            current_invitation.purpose = purpose
                            current_invitation.current_time = datetime.datetime.now()
                            current_invitation.save()

                            # 生成邀请任务信息
                            myprocesstask = ProcessTask()
                            myprocesstask.processrun_id = current_process_run_id
                            myprocesstask.starttime = datetime.datetime.now()
                            myprocesstask.senduser = request.user.username
                            myprocesstask.type = "INFO"
                            myprocesstask.logtype = "PLAN"
                            myprocesstask.state = "1"
                            myprocesstask.content = "创建演练计划。"
                            myprocesstask.save()

                            result["data"] = current_process_run_id
                            result["res"] = "流程计划成功，待开启流程。"
            else:
                result["res"] = "演练结束时间必须填写！"
        else:
            result["res"] = "演练开始时间必须填写！"

        return JsonResponse(result)


def save_modify_invitation(request):
    if request.user.is_authenticated():
        result = {}
        plan_process_run_id = request.POST.get("plan_process_run_id", "")
        start_time = request.POST.get("start_date_modify", "")
        purpose = request.POST.get("purpose_modify", "")
        end_time = request.POST.get("end_date_modify", "")

        try:
            plan_process_run_id = int(plan_process_run_id)
        except:
            raise Http404()

        if start_time:
            if end_time:
                current_invitation = Invitation.objects.filter(
                    process_run_id=plan_process_run_id)
                if current_invitation:
                    current_invitation = current_invitation[0]

                    current_invitation.start_time = start_time
                    current_invitation.end_time = end_time
                    current_invitation.purpose = purpose
                    current_invitation.save()

                    # 生成邀请任务信息
                    myprocesstask = ProcessTask()
                    myprocesstask.processrun_id = plan_process_run_id
                    myprocesstask.starttime = datetime.datetime.now()
                    myprocesstask.senduser = request.user.username
                    myprocesstask.type = "INFO"
                    myprocesstask.logtype = "PLAN"
                    myprocesstask.state = "1"
                    myprocesstask.content = "修改演练计划。"
                    myprocesstask.save()

                    result["data"] = plan_process_run_id
                    result["res"] = "修改流程计划成功，待开启流程。"
                else:
                    result["res"] = "演练计划不存在，请联系客服！"
            else:
                result["res"] = "演练结束时间必须填写！"
        else:
            result["res"] = "演练开始时间必须填写！"

        return JsonResponse(result)


def fill_with_invitation(request):
    if request.user.is_authenticated():
        plan_process_run_id = request.POST.get("plan_process_run_id", "")
        current_invitation = Invitation.objects.filter(
            process_run_id=plan_process_run_id)
        if current_invitation:
            current_invitation = current_invitation[0]
            start_time = current_invitation.start_time
            end_time = current_invitation.end_time
            purpose = current_invitation.purpose
            return JsonResponse({
                "start_time": start_time.strftime('%Y-%m-%d %H:%M:%S') if start_time else "",
                "end_time": end_time.strftime('%Y-%m-%d %H:%M:%S') if end_time else "",
                "purpose": purpose,
            })


def invite(request):
    if request.user.is_authenticated():
        process_id = request.GET.get("process_id", "")
        start_date = request.GET.get("start_date", "")
        purpose = request.GET.get("purpose", "")
        end_date = request.GET.get("end_date", "")
        process_date = start_date
        nowtime = datetime.datetime.now()
        invite_time = nowtime.strftime("%Y-%m-%d")

        current_processes = Process.objects.filter(
            id=process_id).filter(type="falconstor")
        process_name = current_processes[0].name if current_processes else ""
        allgroup = current_processes[0].step_set.exclude(state="9").exclude(Q(group="") | Q(group=None)).values(
            "group").distinct()
        all_groups = ""
        if allgroup:
            for num, current_group in enumerate(allgroup):
                if num == len(allgroup) - 1:
                    group = Group.objects.get(id=int(current_group["group"]))
                    all_groups += group.name
                else:
                    group = Group.objects.get(id=int(current_group["group"]))
                    all_groups += group.name + "、"
        wrapper_step_list = custom_wrapper_step_list(process_id)
        # return render(request, 'notice.html',
        #                      {"wrapper_step_list": wrapper_step_list, "person_invited": person_invited,
        #                       "invite_reason": invite_reason, "invite_time": invite_time})
        t = TemplateResponse(request, 'notice.html',
                             {"wrapper_step_list": wrapper_step_list, "process_date": process_date,
                              "purpose": purpose, "invite_time": invite_time, "start_date": start_date,
                              "end_date": end_date,
                              "process_name": process_name, "all_groups": all_groups})
        t.render()

        current_path = os.getcwd()

        if sys.platform.startswith("win"):
            # 指定wkhtmltopdf运行程序路径
            wkhtmltopdf_path = current_path + os.sep + "faconstor" + os.sep + "static" + os.sep + \
                               "process" + os.sep + "wkhtmltopdf" + os.sep + "bin" + os.sep + "wkhtmltopdf.exe"
            config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
        else:
            config = None

        options = {
            'page-size': 'A3',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8",
            'no-outline': None
        }
        css_path = current_path + os.sep + "faconstor" + \
                   os.sep + "static" + os.sep + "new" + os.sep + "css"
        css_01 = css_path + os.sep + "bootstrap.css"
        # css_02 = css_path + os.sep + "font-awesome.min.css"
        css_03 = css_path + os.sep + "icon.css"
        # css_04 = css_path + os.sep + "font.css"
        css_05 = css_path + os.sep + "app.css"
        css_06 = current_path + os.sep + "faconstor" + os.sep + "static" + os.sep + \
                 "assets" + os.sep + "global" + os.sep + "css" + os.sep + "components.css"

        css = [r"{0}".format(mycss)
               for mycss in [css_01, css_03, css_05, css_06]]

        pdfkit.from_string(t.content.decode(encoding="utf-8"), r"invitation.pdf", configuration=config, options=options,
                           css=css)

        the_file_name = "invitation.pdf"
        response = StreamingHttpResponse(file_iterator(the_file_name))
        response['Content-Type'] = 'application/octet-stream; charset=unicode'
        response['Content-Disposition'] = 'attachment;filename="{0}"'.format(
            the_file_name)
        return response


def get_all_users(request):
    if request.user.is_authenticated():
        all_users = UserInfo.objects.exclude(user=None)
        user_string = ""
        for user in all_users:
            user_string += user.fullname + "&"
        return JsonResponse({"data": user_string})
