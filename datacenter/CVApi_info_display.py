# -*- coding: utf-8 -*-

import sys
import os
import requests
import time
import copy
import subprocess

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element
import base64

try:
    import urllib.request  as urllib
except:
    import urllib


# __platform__ = {"platform":None, "ProcessorType":0, "hostName":None}
# __clientInfo__ = {"clientName":None, "clientId":None, "platform":self.platform, "backupsetList":[], "agentList":[]}


class CV_RestApi_Token(object):
    """
    Class documentation goes here.
    it is CV Rest API

    member
        init
        login(credit) return None/token
        setAccess
    """

    def __init__(self):
        """
        Constructor
        """
        # super().__init__()
        self.service = 'http://<<server>>:<<port>>/SearchSvc/CVWebService.svc/'
        self.credit = {"webaddr": "", "port": "", "username": "", "passwd": "", "token": "", "lastlogin": 0}
        self.isLogin = False
        self.msg = ""
        self.sendText = ""
        self.receiveText = ""

    def getTokenString(self):
        return self.credit["token"]

    def login(self, credit):
        if self.isLogin == False:
            self.credit["token"] = None
            self.credit["lastlogin"] = 0

        try:
            self.credit["webaddr"] = credit["webaddr"]
            self.credit["port"] = credit["port"]
            self.credit["username"] = credit["username"]
            self.credit["passwd"] = credit["passwd"]
            self.credit["token"] = credit["token"]
            self.credit["lastlogin"] = credit["lastlogin"]
        except:
            self.msg = "login information is not correct"
            return None

        if self.credit["token"] != None:
            if self.credit["token"].count("QSDK") == 1:
                diff = time.time() - self.credit["lastlogin"]
                if diff <= 550:
                    return self.credit["token"]

        self.isLogin = self._login(self.credit)
        return self.credit["token"]

    def _login(self, credit):
        """
        Constructor
        login function
        """
        self.isLogin = False
        self.credit["token"] = None
        # print(credit)
        self.service = self.service.replace("<<server>>", self.credit["webaddr"])
        self.service = self.service.replace("<<port>>", self.credit["port"])

        password = base64.b64encode(self.credit["passwd"].encode(encoding="utf-8"))

        loginReq = '<DM2ContentIndexing_CheckCredentialReq mode="Webconsole" username="<<username>>" password="<<password>>" />'
        loginReq = loginReq.replace("<<username>>", self.credit["username"])
        loginReq = loginReq.replace("<<password>>", password.decode())
        self.sendText = self.service + 'Login' + loginReq
        try:
            r = requests.post(self.service + 'Login', data=loginReq)
        except:
            self.msg = "Connect Failed: webaddr " + self.credit["webaddr"] + " port " + self.credit["port"]
            return False
        if r.status_code == 200:
            try:
                root = ET.fromstring(r.text)
            except:
                self.msg = "return string is not formatted"
                return False

            if 'token' in root.attrib:
                self.credit["token"] = root.attrib['token']
                if self.credit["token"].count("QSDK") == 1:
                    self.isLogin = True
                    self.credit["lastlogin"] = time.time()
                    self.msg = "Login Successful"

                    return True
                else:
                    self.msg = "Login Failed: username " + self.credit["username"] + " passwd " + self.credit["passwd"]
        else:
            self.msg = "Connect Failed: webaddr " + self.credit["webaddr"] + " port " + self.credit["port"]

        return False

    def checkLogin(self):
        return self.login(self.credit)


class CV_RestApi(object):
    """
    Class documentation goes here.
    it is CV Rest API
    Base Class for CV RestAPI
    attrib
        service is CV webaddr service string
        msg is error/success msg

    member
        init
        login(credit) return None/token
        setAccess
    """

    def __init__(self, token):
        """
        Constructor
        """
        super(CV_RestApi, self).__init__()
        self.service = 'http://<<server>>:<<port>>/SearchSvc/CVWebService.svc/'
        self.webaddr = token.credit["webaddr"]
        self.port = token.credit["port"]
        self.service = self.service.replace("<<server>>", token.credit["webaddr"])
        self.service = self.service.replace("<<port>>", token.credit["port"])
        self.token = token
        self.msg = ""
        self.sendText = ""
        self.receiveText = ""

    def _rest_cmd(self, restCmd, command, updatecmd=""):
        token = self.token.checkLogin()
        if token == None:
            self.msg = "did not get token"
            return None

        clientPropsReq = self.service + command
        self.sendText = clientPropsReq

        try:
            update = updatecmd.encode(encoding="utf-8")
        except:
            update = updatecmd
        headers = {'Cookie2': token}

        if restCmd == "GET":
            try:
                r = requests.get(clientPropsReq, data=update, headers=headers)
            except:
                self.msg = "Connect Failed: webaddr " + self.webaddr + " port " + self.port
                return None

        if restCmd == "POST":
            try:
                r = requests.post(clientPropsReq, data=update, headers=headers)
            except:
                self.msg = "Connect Failed: webaddr " + self.webaddr + " port " + self.port
                return None

        if restCmd == "PUT":
            try:
                r = requests.put(clientPropsReq, data=update, headers=headers)
            except:
                self.msg = "Connect Failed: webaddr " + self.webaddr + " port " + self.port
                return None

        if restCmd == "DEL":
            try:
                r = requests.delete(clientPropsReq, data=update, headers=headers)
            except:
                self.msg = "Connect Failed: webaddr " + self.webaddr + " port " + self.port
                return None

        if restCmd == "QCMD":
            try:
                r = requests.post(clientPropsReq, data=update, headers=headers)
            except:
                self.msg = "Connect Failed: webaddr " + self.webaddr + " port " + self.port
                return None

        if r.status_code == 200 or r.status_code == 201:
            self.receiveText = r.text
        else:
            self.receiveText = r.status_code
            self.msg = 'Failure: webaddr ' + self.webaddr + " port " + self.port + " retcode: %d" % r.status_code

        return self.receiveText

    def getCmd(self, command, updatecmd=""):
        """
        Constructor
        get command function
        """
        retString = self._rest_cmd("GET", command, updatecmd)
        # if tag:
        #     with open(r"C:\Users\Administrator\Desktop\{0}.xml".format(tag), "w") as f:
        #         f.write(retString)
        try:
            return ET.fromstring(retString)
        except:
            self.msg = "receive string is not XML format"
            return None

    def postCmd(self, command, updatecmd=""):
        """
        Constructor
        get command function
        """
        retString = self._rest_cmd("POST", command, updatecmd)
        try:
            respRoot = ET.fromstring(retString)
            respEle = respRoot.findall(".//response")
            errorCode = ""
            for node in respEle:
                errorCode = node.attrib["errorCode"]
            if errorCode == "0":
                self.msg = "Set successfully"
                return retString
            else:
                try:
                    errString = node.attrib["errorString"]
                    self.msg = "PostCmd:" + command + "ErrCode: " + errorCode + "ErrString:" + errString
                except:
                    self.msg = "post command:" + command + " Error Code: " + errorCode + " receive text is " + self.receiveText
                    pass
            return None
        except:
            self.msg = "receive string is not XML format:" + self.receiveText
            return None

    def delCmd(self, command, updatecmd=""):
        # DELETE <webservice>/Backupset/{backupsetId}
        retString = self._rest_cmd("DELETE", command, updatecmd)
        try:
            respRoot = ET.fromstring(retString)
            respEle = respRoot.findall(".//response")
            errorCode = ""
            for node in respEle:
                errorCode = node.attrib["errorCode"]
            if errorCode == "0":
                self.msg = "Set successfully"
                return True
            self.msg = "del command:" + command + " xml format:" + updatecmd + " Error Code: " + errorCode + " receive text is " + self.receiveText
            return False
        except:
            self.msg = "receive string is not XML format:" + self.receiveText
            return False

    def putCmd(self, command, updatecmd=""):
        # PUT <webservice>/Backupset/{backupsetId}
        retString = self._rest_cmd("PUT", command, updatecmd)
        try:
            respRoot = ET.fromstring(retString)
            respEle = respRoot.findall(".//response")
            errorCode = ""
            for node in respEle:
                errorCode = node.attrib["errorCode"]
            if errorCode == "0":
                self.msg = "Set successfully"
                return retString
            self.msg = "del command:" + command + " xml format:" + updatecmd + " Error Code: " + errorCode + " receive text is " + self.receiveText
            return None
        except:
            self.msg = "receive string is not XML format:" + self.receiveText
            return None

    def qCmd(self, command, updatecmd=""):
        """
        Constructor
        get command function
        """
        retString = self._rest_cmd("QCMD", command, updatecmd)
        try:
            respRoot = ET.fromstring(retString)
            respjob = respRoot.findall(".//jobIds")
            for node in respjob:
                return True
            respEle = respRoot.findall(".//response")
            errorCode = ""
            for node in respEle:
                errorCode = node.attrib["errorCode"]
            if errorCode == "0":
                self.msg = "Set successfully"
                return True
            else:
                try:
                    errString = node.attrib["errorString"]
                    self.msg = "qcmd command:" + command + " Error Code: " + errorCode + " ErrString: " + errString
                except:
                    self.msg = "qcmd command:" + command + " Error Code: " + errorCode + " receive text is " + self.receiveText
                    pass
            return False
        except:
            # traceback.print_exc()
            return retString


class CV_GetAllInformation(CV_RestApi):
    """
    class CV_getAllInformation is get total information class
    include client, subclient, storagePolice, schdule, joblist
    spList = {"storagePolicyId", "storagePolicyName"}
    schduleList = {"taskName", "associatedObjects", "taskType", "runUserId", "taskId", "ownerId", "description", "ownerName", "policyType", "GUID", "alertId"}
    clientList = {"clientId", "clientName", "_type_"}

    getSPlist return storage Police list
    getSchduleList return schdule List
    getClientList return client List
    getJobList return job list

    """

    def __init__(self, token):
        """
        Constructor
        """
        super(CV_GetAllInformation, self).__init__(token)

        self.SPList = []
        self.SchduleList = []
        self.clientList = []
        self.jobList = []
        self.vmClientList = []
        self.vmProxyList = []

        self.vmDCName = []
        self.vmESXHost = []
        self.vmDataStore = []
        self.vmList = []

    def getSPList(self):
        del self.SPList[:]
        client = self.getCmd('StoragePolicy')
        if client == None:
            return None

        activePhysicalNode = client.findall(".//policies")
        for node in activePhysicalNode:
            if node.attrib["storagePolicyId"] <= "2":
                continue
            if "System Create" in node.attrib["storagePolicyName"]:
                continue
            self.SPList.append(node.attrib)
        return self.SPList

    def getSchduleList(self):
        del self.SchduleList[:]
        client = self.getCmd('SchedulePolicy')
        if client == None:
            return None
        activePhysicalNode = client.findall(".//taskDetail/task")
        for node in activePhysicalNode:
            if "System Created " in node.attrib["taskName"]:
                continue
            self.SchduleList.append(node.attrib)
        return self.SchduleList

    def getClientList(self):
        del self.clientList[:]
        clientRec = {"clientName": None, "clientId": -1}
        client = self.getCmd('/Client')
        if client == None:
            return None
        activePhysicalNode = client.findall(".//clientEntity")
        for node in activePhysicalNode:
            rec = copy.deepcopy(clientRec)
            rec["clientName"] = node.attrib["clientName"]
            try:
                rec["clientId"] = int(node.attrib["clientId"])
            except:
                pass
            self.clientList.append(rec)
        return self.clientList

    def getJobList(self, clientId, type="backup", appTypeName=None, backupsetName=None, subclientName=None, start=None,
                   end=None):
        statusList = {"Running": "运行", "Waiting": "等待", "Pending": "阻塞", "Suspend": "终止", "commpleted": "完成",
                      "Failed": "失败", "Failed to Start": "启动失败", "Killed": "杀掉"}
        '''
        Running
        Waiting
        Pending
        Suspend
        Kill Pending
        Interrupt Pending
        Interrupted
        QueuedCompleted
        Completed w/ one or more errors
        Completed w/ one or more warnings
        Committed
        Failed
        Failed to Start
        Killed
        '''
        del self.jobList[:]

        command = "/Job?clientId=<<clientId>>"
        param = ""
        if type != None:
            param = "&jobFilter=<<type>>"
        cmd = command + param
        cmd = cmd.replace("<<clientId>>", clientId)
        cmd = cmd.replace("<<type>>", type)
        resp = self.getCmd(cmd)

        if resp == None:
            return None

        # print(resp)
        # print(self.receiveText)
        activePhysicalNode = resp.findall(".//jobs/jobSummary")
        for node in activePhysicalNode:
            # if start != None:
            # if end != None:
            # print(node.attrib)
            if appTypeName != None:
                if appTypeName not in node.attrib["appTypeName"]:
                    continue;
            if backupsetName != None:
                if backupsetName not in node.attrib["backupSetName"]:
                    continue;
            if subclientName != None:
                if subclientName not in node.attrib["subclientName"]:
                    continue;
            status = node.attrib["status"]
            try:
                node.attrib["status"] = statusList[status]
            except:
                node.attrib["status"] = status
            self.jobList.append(node.attrib)
        return self.jobList

    def checkRunningJob(self, clientName, appType, backupsetName, instanceName):
        command = "QCommand/qlist job -c <<clientName>> -format xml"
        command = command.replace("<<clientName>>", clientName)
        retString = self.postCmd(command)
        try:
            resp = ET.fromstring(retString)
        except:
            self.msg = "qlist job xml format is error"
            return False
        # print(clientName, appType, backupsetName, instanceName)
        jobitems = resp.findall(".//jobs")
        for node in jobitems:
            attrib = node.attrib
            # print(attrib, clientName, appType, backupsetName, instanceName)
            if attrib["clientName"] == clientName:
                # if attrib["appName"] == appType:
                if attrib["backupSetName"] == backupsetName or backupsetName == None:
                    if attrib["instanceName"] == instanceName or instanceName == None:
                        return True

        return False


class CV_Client(CV_GetAllInformation):
    def __init__(self, token, client=None):
        """
        Constructor
        """
        super(CV_Client, self).__init__(token)
        self.client = client
        self.backupsetList = []
        self.subclientList = []
        self.platform = {"platform": None, "ProcessorType": 0, "hostName": None}
        self.clientInfo = {"clientName": None, "clientId": None, "platform": self.platform, "backupsetList": [],
                           "agentList": []}
        # self.backupInfo = {"clientId":None, "clientName":None, "agentType":None, "agentId":None, "backupsetId":None,
        # "backupsetName":None, "instanceName":None, "instanceId":None}

        self.isNewClient = True
        self.getClientInfo(client)
        self.schedule_description = []

    def getClient(self, client):
        # get clientName and clientId
        clientInfo = self.clientInfo
        if isinstance(client, (int)):
            command = "Client/<<client>>"
            command = command.replace("<<client>>", str(client))
            resp = self.getCmd(command)
            if resp == None:
                return False
            clientEntity = resp.findall(".//clientEntity")
            if clientEntity == []:
                return False

            clientInfo["clientId"] = clientEntity[0].attrib["clientId"]
            clientInfo["clientName"] = clientEntity[0].attrib["clientName"]
        else:
            command = "GetId?clientName=<<client>>"
            command = command.replace("<<client>>", client)
            resp = self.getCmd(command)
            if resp == None:
                return False

            clientInfo["clientId"] = resp.attrib["clientId"]
            if int(clientInfo["clientId"]) <= 0:
                return False
            clientInfo["clientName"] = resp.attrib["clientName"]
        return True

    def getSubClientList(self, clientId):
        # subclientInfo {'subclientName','instanceName','backupsetName','appName','applicationId','clientName',
        # 'instanceId','backupsetId','subclientId', 'clientId'}
        subList = self.subclientList
        del subList[:]
        if clientId == None:
            return None
        cmd = 'Subclient?clientId=<<clientId>>'
        cmd = cmd.replace("<<clientId>>", clientId)
        subclient = self.getCmd(cmd)
        if subclient == None:
            return None
        activePhysicalNode = subclient.findall(".//subClientEntity")
        for node in activePhysicalNode:
            subList.append(node.attrib)
        return subList

    def getBackupsetList(self, clientId):
        self.getSubClientList(clientId)
        flag = 0
        del self.backupsetList[:]
        backupsetInfo = {"clientId": -1, "clientName": None, "agentType": None, "agentId": None, "backupsetId": -1,
                         "backupsetName": None, "instanceName": None, "instanceId": -1}
        for node in self.subclientList:
            # backupsetId = int(node["backupsetId"])
            flag = 0
            for item in self.backupsetList:
                if node["backupsetId"] == item["backupsetId"]:
                    flag = 1
                    break
            if flag == 1:
                continue
            backupset = copy.deepcopy(backupsetInfo)
            backupset["clientName"] = node["clientName"]
            backupset["agentType"] = node["appName"]
            backupset["backupsetName"] = node["backupsetName"]
            backupset["instanceName"] = node["instanceName"]
            backupset["backupsetId"] = node["backupsetId"]
            backupset["instanceId"] = node["instanceId"]
            backupset["clientId"] = node["clientId"]
            backupset["subclientId"] = node["subclientId"]

            self.backupsetList.append(backupset)
        return self.backupsetList

    def getClientOSInfo(self, clientId):
        if clientId == None:
            return None
        command = "Client/<<clientId>>"
        command = command.replace("<<clientId>>", clientId)
        resp = self.getCmd(command)

        try:
            osinfo = resp.findall(".//OsDisplayInfo")
            self.platform["platform"] = osinfo[0].attrib["OSName"]
            self.platform["ProcessorType"] = osinfo[0].attrib["ProcessorType"]

            hostnames = resp.findall(".//clientEntity")
            self.platform["hostName"] = hostnames[0].attrib["hostName"]
        except:
            self.msg = "error get client platform"

    def getClientInstance(self, clientId):
        instance = {}
        myproxylist = []
        if clientId == None:
            return None
        command = "/instance?clientId=<<clientId>>"
        command = command.replace("<<clientId>>", clientId)
        resp = self.getCmd(command)

        try:
            vcinfo = resp.findall(".//vmwareVendor/virtualCenter")
            instance["HOST"] = vcinfo[0].attrib["domainName"]
            instance["USER"] = vcinfo[0].attrib["userName"]

            proxylist = resp.findall(".//memberServers/client")
            for proxy in proxylist:
                myproxylist.append({"clientId": proxy.attrib["clientId"], "clientName": proxy.attrib["clientName"]})
            instance["PROXYLIST"] = myproxylist
        except:
            self.msg = "error get client instance"
        return instance

    def getClientAgentList(self, clientId):
        agentList = []
        agent = {}
        if clientId == None:
            return None
        command = "Agent?clientId=<<clientId>>"
        command = command.replace("<<clientId>>", clientId)
        resp = self.getCmd(command)
        # print(self.receiveText)
        try:
            activePhysicalNode = resp.findall(".//idaEntity")
            for node in activePhysicalNode:
                # print("agent list")
                # print(node.attrib)
                agent["clientName"] = node.attrib["clientName"]
                agent["agentType"] = node.attrib["appName"]
                agent["appId"] = node.attrib["applicationId"]
                agentList.append(copy.deepcopy(agent))
        except:
            self.msg = "error get agent type"
            pass
        return agentList

    def getClientInfo(self, client):
        self.isNewClient = True

        if self.token == None or client == None:
            return None
        # get client
        if self.getClient(client) == False:
            return None
        clientInfo = self.clientInfo
        # 客户端安装时间
        self.isNewClient = False
        # get backupsetList
        clientInfo["backupsetList"] = self.getBackupsetList(clientInfo["clientId"])
        # get platform
        self.getClientOSInfo(clientInfo["clientId"])
        # get agent list
        clientInfo["agentList"] = self.getClientAgentList(clientInfo["clientId"])
        if (clientInfo["platform"]["platform"]).upper() == "ANY":
            clientInfo["instance"] = self.getClientInstance(clientInfo["clientId"])
        return clientInfo

    def getIsNewClient(self):
        return self.isNewClient

    def getSubclientInfo(self, subclientId):
        backupInfo = {}
        mycontent = []
        if subclientId == None:
            return None
        command = "/Subclient/<<subclientId>>"
        command = command.replace("<<subclientId>>", subclientId)
        resp = self.getCmd(command)
        try:
            subClientEntity = resp.findall(".//subClientEntity")
            # 应用名
            backupInfo["appName"] = subClientEntity[0].get("appName", "")
            # 存储策略
            dataBackupStoragePolicy = resp.findall(".//dataBackupStoragePolicy")

            # 存储策略具体内容
            storagePolicyId = dataBackupStoragePolicy[0].get("storagePolicyId", "")
            storage_policy_cmd = "/StoragePolicy/{0}?propertyLevel=10".format(storagePolicyId)
            storage_policy_xml = self.getCmd(storage_policy_cmd)
            storage_policy_copy = storage_policy_xml.findall(".//StoragePolicyCopy") if storage_policy_xml else []
            storage_library = storage_policy_xml.findall(".//library") if storage_policy_xml else []
            storage_drive_pool = storage_policy_xml.findall(".//drivePool") if storage_policy_xml else []
            storage_retention_rules = storage_policy_xml.findall(".//retentionRules") if storage_policy_xml else []

            backupInfo["storage_info"] = {
                "storage_id": dataBackupStoragePolicy[0].get("storagePolicyId", ""),
                "storage_name": dataBackupStoragePolicy[0].get("storagePolicyName", ""),
                "storage_policy_copy": dict(storage_policy_copy[0].items()) if storage_policy_copy else "",
                "storage_library": dict(storage_library[0].items()) if storage_library else "",
                "storage_drive_pool": dict(storage_drive_pool[0].items()) if storage_drive_pool else "",
                "storage_retention_rules": dict(storage_retention_rules[0].items()) if storage_retention_rules else "",
            }
            # 计划策略
            schduleList = []
            cmd = "Schedules?subclientId=<<subclientId>>"
            cmd = cmd.replace("<<subclientId>>", subclientId)
            client = self.getCmd(cmd)
            try:
                activePhysicalNode = client.findall(".//task")
                for node in activePhysicalNode:
                    schduleList.append(node.attrib)
            except:
                self.msg = "did not get Task"
            schedule_policy_list = []
            for schedule in schduleList:
                task_id = schedule["taskId"] if schduleList else ""

                # 计划策略具体内容
                cmd_get_schedule_name = "SchedulePolicy/{0}".format(task_id)
                content = self.getCmd(cmd_get_schedule_name)
                schedule_info = content.findall(".//pattern") if content else []
                if schedule_info:
                    schedule_info = schedule_info[0]
                    schedule_policy_dict = dict(schedule_info.items())
                    schedule_policy_dict["schdule_name"] = schduleList[0]["taskName"] if schduleList else ""

                    schedule_policy_list.append(schedule_policy_dict)
            backupInfo["schedule_info"] = schedule_policy_list

            # 客户端备份内容
            # 文件备份集信息
            if backupInfo["appName"] == "File System":
                # content
                contentlist = resp.findall(".//content")
                for content in contentlist:
                    mycontent.append(content.get("path", ""))
                backupInfo["content"] = mycontent
                # backupSystemState
                fsSubClientProp = resp.findall(".//fsSubClientProp")
                backupInfo["backupSystemState"] = fsSubClientProp[0].get("backupSystemState", "")
                if backupInfo["backupSystemState"] == "0" or backupInfo["backupSystemState"] == "false":
                    backupInfo["backupSystemState"] = "FALSE"
                if backupInfo["backupSystemState"] == "1" or backupInfo["backupSystemState"] == "true":
                    backupInfo["backupSystemState"] = "TRUE"
            # 数据库实例信息
            if backupInfo["appName"] == "SQL Server":
                command = "/instance?clientId=<<clientId>>"
                command = command.replace("<<clientId>>", subClientEntity[0].get("clientId", ""))
                resp = self.getCmd(command)
                instancenodes = resp.findall(".//instanceProperties")
                for instancenode in instancenodes:
                    instance = instancenode.findall(".//instance")

                    if instance[0].get("instanceId", "") == subClientEntity[0].get("instanceId", ""):
                        backupInfo["instanceName"] = instance[0].get("instanceName", "")
                        mssqlInstance = instancenode.findall(".//mssqlInstance")
                        backupInfo["vss"] = mssqlInstance[0].get("useVss", "")
                        if backupInfo["vss"] == "0" or backupInfo["vss"] == "false":
                            backupInfo["vss"] = "FALSE"
                        if backupInfo["vss"] == "1" or backupInfo["vss"] == "true":
                            backupInfo["vss"] = "TRUE"

                        # iscover
                        iscover = instancenode.findall(".//mssqlInstance/overrideHigherLevelSettings")
                        if iscover:
                            iscover = iscover[0]
                            backupInfo["iscover"] = iscover.get("overrideGlobalAuthentication", "")
                        else:
                            backupInfo["iscover"] = ""

                        if backupInfo["iscover"] == "0" or backupInfo["iscover"] == "false":
                            backupInfo["iscover"] = "FALSE"
                        if backupInfo["iscover"] == "1" or backupInfo["iscover"] == "true":
                            backupInfo["iscover"] = "TRUE"
                        # user:<userAccount/>
                        userAccount = instancenode.findall(".//mssqlInstance/overrideHigherLevelSettings/userAccount")
                        if userAccount:
                            backupInfo["userName"] = userAccount[0].get("userName", "")
                        else:
                            backupInfo["userName"] = ""
                        break
            if backupInfo["appName"] == "Oracle":
                command = "/instance?clientId=<<clientId>>"
                command = command.replace("<<clientId>>", subClientEntity[0].get("clientId", ""))
                resp = self.getCmd(command)
                instancenodes = resp.findall(".//instanceProperties")
                for instancenode in instancenodes:
                    instance = instancenode.findall(".//instance")
                    if instance[0].get("instanceId", "") == subClientEntity[0].get("instanceId", ""):
                        backupInfo["instanceName"] = instance[0].get("instanceName", "")
                        oracleInstance = instancenode.findall(".//oracleInstance")
                        backupInfo["oracleHome"] = oracleInstance[0].get("oracleHome", "")
                        oracleUser = instancenode.findall(".//oracleInstance/oracleUser")
                        backupInfo["oracleUser"] = oracleUser[0].get("userName", "")
                        # connect
                        sqlConnect = instancenode.findall(".//oracleInstance/sqlConnect")
                        backupInfo["conn1"] = sqlConnect[0].get("userName", "")
                        backupInfo["conn2"] = ""  # sys密码，没有
                        backupInfo["conn3"] = sqlConnect[0].get("domainName", "")
                        break
            if backupInfo["appName"] == "Virtual Server":
                children = resp.findall(".//vmContent/children")
                for child in children:
                    mycontent.append(child.get("displayName", ""))
                backupInfo["content"] = mycontent
                backupInfo["backupsetName"] = subClientEntity[0].get("backupsetName", "")
        except:
            self.msg = "error get client instance"
        return backupInfo


class CV_API(object):
    """
    commvault自定义接口
    """

    def __init__(self, cvToken):
        """
        Constructor
        """
        super(CV_API, self).__init__()
        self.token = cvToken
        self.msg = None

    def getClientList(self):
        """
        获取客户端列表
        :return:
        """
        info = CV_GetAllInformation(self.token)
        list = info.getClientList()
        self.msg = info.msg
        return list

    def getClientInfo(self, client):
        clientInfo = CV_Client(self.token)
        info = clientInfo.getClientInfo(client)
        self.msg = clientInfo.msg
        return info

    def getJobList(self, client, agentType=None, backupset=None, type="backup"):
        """
        作业列表
        :param client:
        :param agentType:
        :param backupset:
        :param type:
        :return:
        """
        joblist = []
        jobRec = {}
        info = CV_GetAllInformation(self.token)
        clientRec = CV_Client(self.token, client)
        list = info.getJobList(clientId=clientRec.clientInfo["clientId"], type=type, appTypeName=agentType,
                               backupsetName=backupset, subclientName=None, start=None, end=None)

        for node in list:
            jobRec["jobId"] = node["jobId"]
            jobRec["status"] = node["status"]
            jobRec["client"] = clientRec.clientInfo["clientName"]
            jobRec["agentType"] = node["appTypeName"]
            jobRec["backupSetName"] = node["backupSetName"]
            # jobRec["destClient"] = node["destClientName"]
            jobRec["jobType"] = node["jobType"]
            jobRec["Level"] = node["backupLevel"]
            # 流量
            jobRec["appSize"] = node["sizeOfApplication"]
            # 磁盘容量
            jobRec["diskSize"] = node["sizeOfMediaOnDisk"]
            jobRec["StartTime"] = node["jobStartTime"]
            jobRec["LastTime"] = node["lastUpdateTime"]
            joblist.append(copy.deepcopy(jobRec))
        self.msg = info.msg
        return joblist

    def getSubclientInfo(self, subclientId):
        """
        备份内容统计
        :param subclientId:
        :return:
        """
        clientInfo = CV_Client(self.token)
        return clientInfo.getSubclientInfo(subclientId)

    def get_backup_info_by_client(self, client):
        """
        根据client_id获取所有备份信息：
        {
            "agent_list": [{
                "backup_set_list": [{
                    "sub_client_list": [{
                        "sub_client_id": "7",
                        "storage_info": {
                            "storage_drive_pool": {
                                "drivePoolId": "1",
                                "__type__": "47",
                                "drivePoolName": "DrivePool(win2008)1"
                            },
                            "storage_retention_rules": {
                                "retainBackupDataForDays": "-1",
                                "jobs": "0",
                                "retainBackupDataForCycles": "-1",
                                "retainArchiverDataForDays": "-1",
                                "retentionFlags": "2"
                            },
                            "storage_library": {
                                "libraryName": "test_disk",
                                "libraryId": "1",
                                "__type__": "9"
                            },
                            "storage_policy_copy": {
                                "copyId": "2",
                                "__type__": "18",
                                "copyName": "\u4e3b"
                            },
                            "storage_name": "test_storage_policy",
                            "storage_id": "3"
                        },
                        "schedule_info": [{
                            "freq_interval": "127",
                            "active_end_occurence": "0",
                            "active_start_time": "00:00:00",
                            "active_end_time": "23:59:00",
                            "freq_restart_interval": "0",
                            "active_end_date": "0",
                            "skipDayNumber": "0",
                            "freq_relative_interval": "0",
                            "name": "",
                            "description": "",
                            "freq_subday_interval": "28800",
                            "patternId": "7",
                            "active_start_date": "2013-01-14 08:00:00",
                            "flags": "0",
                            "schdule_name": "System Created for DDB subclients",
                            "freq_recurrence_factor": "1",
                            "skipOccurence": "0",
                            "freq_type": "Weekly"
                        }]
                    }],
                    "back_up_set_id": "3",
                    "back_up_set_name": "defaultBackupSet"
                }],
                "agent_type": "File System"
            }]
        }
        :return: backup_info_by_client
        """
        cv_client = CV_Client(self.token)
        c_agent_list = cv_client.getClientAgentList(client)

        backup_info_by_client = {}
        agent_list = []
        for agent in c_agent_list:
            agent_info = {}
            agent_type = agent["agentType"]

            c_backup_set_list = cv_client.getBackupsetList(client)

            backup_set_list = []
            for backup_set in c_backup_set_list:
                if agent_type == backup_set["agentType"]:
                    backup_set_info = dict()
                    backup_set_info["back_up_set_id"] = backup_set["backupsetId"]
                    backup_set_info["back_up_set_name"] = backup_set["backupsetName"]

                    sub_client_list = []
                    c_sub_client_list = cv_client.getSubClientList(client)
                    for sub_client in c_sub_client_list:
                        if backup_set_info["back_up_set_id"] == sub_client["backupsetId"]:
                            # backup_set_id相同
                            sub_client_id = sub_client["subclientId"]
                            c_sub_client_info = cv_client.getSubclientInfo(sub_client_id)
                            sub_client_info = dict()
                            sub_client_info["sub_client_id"] = sub_client_id
                            # sub_client_info["schedule"] = c_sub_client_info["schedule_name"]
                            sub_client_info["schedule_info"] =  ["schedule_info"]

                            # sub_client_info["storage"] = c_sub_client_info["Storage"]
                            sub_client_info["storage_info"] = c_sub_client_info["storage_info"]
                            sub_client_list.append(sub_client_info)

                    backup_set_info["sub_client_list"] = sub_client_list

                    backup_set_list.append(backup_set_info)

            agent_info["agent_type"] = agent_type
            agent_info["backup_set_list"] = backup_set_list
            agent_list.append(agent_info)
        backup_info_by_client["agent_list"] = agent_list

        return backup_info_by_client


if __name__ == "__main__":
    # commvault-10
    info = {"webaddr": "192.168.1.121", "port": "81", "username": "admin", "passwd": "admin", "token": "",
            "lastlogin": 0}
    # info = {"webaddr": "cv-server", "port": "81", "username": "admin", "passwd": "Admin@2017", "token": "",
    #         "lastlogin": 0}
    # info = {"webaddr": "cv-server", "port": "81", "username": "cvadmin", "passwd": "1qaz@WSX", "token": "",
    #         "lastlogin": 0}
    cvToken = CV_RestApi_Token()

    cvToken.login(info)
    cvAPI = CV_API(cvToken)
    # ret = cvAPI.getJobList(3)  # backup status
    ret = cvAPI.get_backup_info_by_client("2")  # 备份策略统计
    # ret = cvAPI.getClientList()
    # ret = cvAPI.getSubclientInfo("34")
    print("***********************", "\n", ret)
    # import json
    #
    # with open(r"C:\Users\Administrator\Desktop\json\2.json", "w") as f:
    #     f.write(json.dumps(ret))
