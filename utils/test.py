import clr
import json
import os, sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.join(BASE_DIR, 'utils'), 'dlls'))
strat_time = "2020-04-28 00:00:00"
end_time = "2020-04-28 00:00:00"
clr.AddReference('PIApp')
from PIApp import *

conn = '10.150.106.40'
tag = 'DCSCOM.Y0GAC11CF101'
curvalue = json.loads(ManagePI.ReadHisValueFromPI(conn, tag, strat_time))
print(curvalue)
# curvalue=json.loads(ManagePI.ReadAvgValueFromPI(conn,tag,strat_time,end_time))
# print(curvalue)
# valuetable=ManagePI.ReadDatetableFromPI(conn,tag,strat_time,end_time,100)
# print(valuetable)
# curvalue=json.loads(ManagePI.ReadHisValueFromPI(conn,tag, strat_time))
# print(curvalue)