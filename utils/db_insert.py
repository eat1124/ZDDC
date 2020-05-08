import sys
from django.core.wsgi import get_wsgi_application
import os
os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'
import cx_Oracle
# 获取django路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.extend([r'%s' % BASE_DIR, ])
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ZDDC.settings")
application = get_wsgi_application()
from datacenter.models import *
from collections import OrderedDict
import decimal
import logging
logger = logging.getLogger('db_insert')

# 查询Oracle表数据
# 插入Target表中
cycle_dict = {
    "SJLX01": 10,
    "SJLX02": 11,
    "SJLX03": 12,
    "SJLX04": 14
}

operate_type_dict = {
    "CZLX01": 15,
    "CZLX02": 16,
    "CZLX03": 17,
}

work_type_dict = {
    'ZBLX01': 28,
    'ZBLX02': 34,
    'ZBLX03': 35,
    'ZBLX04': 36,
    'ZBLX05': 37,
    'ZBLX06': 38,
    'ZBLX07': 39,
    'ZBLX08': 40,
    'ZBLX09': 41,
    'ZBLX10': 42,
    'ZBLX11': 43,
    'ZBLX12': 44,
    'ZBLX13': 45,
    'ZBLX14': 46,
    'ZBLX15': 47,
    'ZBLX16': 48,
}

jz_dict = {
    '03': 49,
    '04': 50,
    '05': 51,
    '06': 52,
    '11': 53,
    '12': 54,
    '00': 30,
}

work_dict = {
    'SSBB03': 9,
    'SSBB04': 10,
    'SSBB06': 11,
    'SSBB01': 12,
    'SSBB02': 13,
    'SSBB05': 14,
    'SSBB07': 15,
    'SSBB00': 16,
}

lj_type = {
    '1': 'jqpj',
    '2': 'qh',
    '3': 'sspj',
}

cumulative_dict = {
    "01": '是',
    "02": '否'
}

sql = 'SELECT * FROM "JYTJ_XTWH_ZBFL"'
tmp = []
# connection = cx_Oracle.connect('abc/Passw0rD@192.168.225.102/dg2')
connection = cx_Oracle.connect('hbmis/hbmis@10.150.99.3/EMIS')
# connection = cx_Oracle.connect('datacenter/datacenter@10.150.85.80/datacent')
cursor = connection.cursor()
cursor.execute(sql)
ret = cursor.fetchall()
cols = [d[0] for d in cursor.description]
for row in ret:
    b = OrderedDict(zip(cols, row))
    tmp.append(b)
cursor.close()
connection.close()
print(tmp[0])
# {'CT_SSJZ': '06', 'CT_KYX': '01', 'CT_OTHER2': None, 'CT_SSBB': 'SSBB03', 'CT_OTHER3': None, 'CT_NAME': '#6机组脱硫剂用量',
# 'AM_SORT2': 1934, 'AM_MIN': 0.0, 'AM_SORT1': 0, 'CT_SBJT': 'yes', 'CT_ZBLX': 'ZBLX01', 'CT_SJLX': 'SJLX02', 'CT_LJTYPE': '2',
# 'AM_JSSX': 4, 'CT_IFCX': 'yes', 'AM_BEIL': 1.0, 'CT_LJJS': '01', 'CT_JSLX': None, 'CT_FACTORY': 'SSDW01', 'AM_TZXS': 1.0, 'CT_CCWZ':
# 'CCWZ06', 'AM_MAX': 9999999999.0, 'CT_CCGZ': None, 'CT_OTHER1': None, 'CT_ID': 'zhfd14061200005', 'CT_SISPOINT': None, 'CT_TYPE':
# 'CZLX03', 'CT_CODE': '6shs'}

# 处理数据
# name code operationtype cycletype businesstype unit magnification cumulative(是) adminapp(6) datatype(numbervalue)
# work_id cumulate_type

insert_data = []

for t in tmp:
    insert_dict = {}
    try:
        for k, v in t.items():
            if k == 'CT_NAME':
                # 指标名称
                insert_dict['name'] = v
            if k == 'CT_CODE':
                # 指标代码
                insert_dict['code'] = v
            if k == 'CT_TYPE':
                # 去除单指标录入操作类型 *****
                if v == 'CZLX04':
                    # 清空insert_dict
                    insert_dict = {}
                    break
                # 操作类型
                insert_dict['operationtype'] = str(operate_type_dict[v])
            if k == 'CT_SJLX':
                # 周期类型
                insert_dict['cycletype'] = str(cycle_dict[v])
            if k == 'CT_ZBLX':
                # 业务类型
                insert_dict['businesstype'] = str(work_type_dict[v])
            if k == 'CT_SSJZ':
                # 去除 03/04/05/06机组信息 *****
                if v in ['03', '04', '05', '06']:
                    insert_dict = {}
                    break
                # 机组
                insert_dict['unit'] = str(jz_dict[v])
            if k == 'AM_BEIL':
                # 倍率
                insert_dict['magnification'] = decimal.Decimal(str(v))
            if k == 'CT_LJJS':
                # 是否累计
                insert_dict['cumulative'] = cumulative_dict[v]
            if k == 'CT_LJTYPE':
                # 累计类型
                insert_dict['cumulate_type'] = lj_type[v]
            insert_dict['adminapp_id'] = 6
            insert_dict['datatype'] = 'numbervalue'
            if k == 'CT_SSBB':
                # 业务ID
                insert_dict['work_id'] = work_dict[v]
    except Exception as e:
        logger.info('id:{id}的数据插入失败，原因是{error}'.format(id=t['CT_ID'], error=e))
    if insert_dict:
        insert_data.append(Target(**insert_dict))
# print(len(insert_data))
try:
    Target.objects.bulk_create(insert_data)
except Exception as e:
    logger.info('批量插入失败，原因是{error}'.format(error=e))
