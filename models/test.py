# -*- coding: utf-8 -*-
__author__ = 'hq-wangxutao'

from xml.dom import minidom
import re
import ssl
#from  urllib.request import  Request,urlopen
from urllib2 import Request,urlopen
import base64
import time
import urllib
import requests
import json
import random
#from  django.db import connection




class CMCS():

    # 初始化， 示例如下，如果不是推送配置，参数可以不用填写
    #ip 与命令可以是多对多，请务必仔细填写
    # cmsc_xml = CMCS('jobName',[{'IPAddrArr':['11.12.68.104'],'commandArr':['show int bri','show inr']}])
    def __init__(self, job_name='',device_ip_command_list={}):
        REQUEST__SUCCESS = 0
        TOKEN__FAIL = 1
        REQUEST__FAIL = 2
        XML_FAIL = 3
        REQUEST__SUCCESS_STORAGE_FAIL = 4
        # coment by nt
        #self.context = ssl._create_unverified_context()
        self.job_name = job_name
        self.dom =  minidom.getDOMImplementation().createDocument(None, "Request", None)
        self.device_ip_command_list = device_ip_command_list


    def __str__(self):
        return self.job_name+':'+self.device_ip_command_list


    #根据参数生成推送给cmcs的xml文。
    def make_job_xml(self):
        requestId = str(time.time()).replace('.','')
        configMapArr = self.makeConfigMapArr(self.device_ip_command_list)
        root = self.dom.documentElement
        root.setAttribute("requestId", requestId)
        jobNode = self.dom.createElement("Job")
        saveDraftNode = self.dom.createElement("SaveDraft")
        applyConfigJobListNode = self.dom.createElement("ApplyConfigJobList")
        applyConfigJobNode = self.dom.createElement("ApplyConfigJob")
        applyConfigJobNode.setAttribute("jobName", self.job_name)
        configMapListNode = self.dom.createElement("ConfigMapList")

        for configMap in configMapArr:
            configMapListNode.appendChild(self.makeConfigMapNode(configMap["IPAddrArr"], configMap["commandArr"]))

        applyConfigJobNode.appendChild(configMapListNode)
        applyConfigJobListNode.appendChild(applyConfigJobNode)
        saveDraftNode.appendChild(applyConfigJobListNode)
        jobNode.appendChild(saveDraftNode)
        root.appendChild(jobNode)
        #root.appendChild(requestNode)

        bytes =  self.dom.toprettyxml(encoding='UTF-8')
        return  bytes.decode("UTF-8")


    #推送给cmcs，地址默认已经填写好。
    def push_to_cmcs(self,url =  "https://22.122.32.128:8001/nccmws/api/v1/Request"):
        token =self.get_token()
        if token== "NO Token" :
            #print("token请求失败")
            return self.TOKEN__FAIL
        authheader = "Bearer " +token
        #request进行包装
        #data = urllib.parse.urlencode({'request':self.make_job_xml()})
        data = urllib.urlencode({'request':self.make_job_xml()})
        data = data.encode('ascii')
        #xmlstr = quote(xml,safe='')

        # modified by nt
        # req = Request(url=url, method="POST")
        req = Request(url=url) 
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        req.add_header("Authorization", authheader)
        req.add_header("Cache-Control", "no-cache")


        #进行请求并返回REQUEST__SUCCESS =0 请求成功
        """
        try:
            #response = urlopen(req,data,context=self.context)
            response = urlopen(req,data)
            result = response.read().decode("UTF-8")
            if result.find("ApplyConfigJob></SaveDra")!=-1 :
                return  self.REQUEST__SUCCESS
            else:
                root = minidom.parseString(result)._get_documentElement()
                ErrorMessage = root.getElementsByTagName('ErrorMessage')
                err_message = ErrorMessage[0].childNodes[0].nodeValue
                #print(err_message)
                return err_message
        except Exception as e :
            #print(e)
            return  self.REQUEST__FAIL
        """
        #response = urlopen(req,data,context=self.context)
        response = urlopen(req,data)
        result = response.read().decode("UTF-8")
        print result
        if result.find("ApplyConfigJob></SaveDra")!=-1 :
            return  self.REQUEST__SUCCESS
        else:
            root = minidom.parseString(result)._get_documentElement()
            ErrorMessage = root.getElementsByTagName('ErrorMessage')
            err_message = ErrorMessage[0].childNodes[0].nodeValue
            #print(err_message)
            return err_message






########################below is some shortcut  function #############
    def get_token(self,url="https://22.122.32.128:8001/nccmws/api/v1/Token", username = "apitest1",password = "Cisco123"):
           #加密用户名密码
            s = username+':'+ password
            s=s.encode("utf-8")
            base64string = base64.encodestring(s)
            authheader = "Basic " + base64string.decode("utf-8")
            authheader = authheader.replace('\n','')
            #request进行包装
            #req = Request(url=url,method="GET")
            req = Request(url=url)
            req.add_header("Authorization", authheader)
            req.add_header("Content-Type", "application/x-www-form-urlencoded")
            req.add_header("grant-type","client_credentials")
            req.add_header("Cache-Control","no-cache")

            #进行请求并返回token
            try:
                #response = urlopen(req,context=self.context)
                response = urlopen(req)
                token = response.read()
                temp = token.decode("utf-8")
                token_dict = temp.split(" ")
                token = {"access_token":token_dict[1],"timestamp":time.time()}
            except Exception as e  :
                #print(e)
                token = {"access_token":"No Token","timestamp":time.time()}
            if token['access_token'] !='No Token':
                return token['access_token']
            return "geting token failded"

    def makeConfigMapNode(self,IPAddrArr, commandArr):
        configMapNode = self.dom.createElement("ConfigMap")
        configMapNode.appendChild(self.makeDeviceSelection(IPAddrArr))
        configMapNode.appendChild(self.makeCLIList(commandArr))
        return configMapNode


    def makeDeviceSelection(self,IPAddrArr):
        deviceSelectionNode = self.dom.createElement("DeviceSelection")
        deviceListNode = self.dom.createElement("DeviceList")
        for IPAddr in IPAddrArr:
            deviceNode = self.dom.createElement("Device")
            IPAddressNode = self.dom.createElement("IPAddress")
            customerNode = self.dom.createElement("Customer")
            IPAddrTextNode = self.dom.createTextNode(IPAddr)
            IPAddressNode.appendChild(IPAddrTextNode)
            customerTetxNode = self.dom.createTextNode("BOC")
            customerNode.appendChild(customerTetxNode)
            deviceNode.appendChild(IPAddressNode)
            deviceNode.appendChild(customerNode)
            deviceListNode.appendChild(deviceNode)
        deviceSelectionNode.appendChild(deviceListNode)
        return  deviceSelectionNode

    def makeCLIList(self,commandArr):
        CLIListNode = self.dom.createElement("CLIList")
        for command in commandArr:
            CLINode = self.dom.createElement("CLI")
            commandNode = self.dom.createElement("Command")
            commandTetxNode = self.dom.createTextNode(command)
            commandNode.appendChild(commandTetxNode)
            CLINode.appendChild(commandNode)
            CLIListNode.appendChild(CLINode)
        return  CLIListNode

    def makeConfigMapArr(self,device_ip_command_list):
        configMapArr = []
        for device_ip_command in self.device_ip_command_list:
            IPAddrArr = device_ip_command['IPAddrArr']
            commandArr = device_ip_command['commandArr']
            configMapArr.append(self.makeConfigMap(IPAddrArr, commandArr))

        return configMapArr

    def makeConfigMap(self,IPAddrArr, commandArr):
        configMap = {
            "IPAddrArr":IPAddrArr,
            "commandArr":commandArr
        }
        return configMap


def getdata_from_res(data_url):
    data = requests.post(data_url)
    return data.text
    
if __name__ == '__main__':
    data=getdata_from_res('http://22.1.111.29:5000/config/SM-HQ-20141205-7777')
    data_orgs = json.loads(data)
    
    datas_to_dev = []
    dev_dic = {}
    for data_org in data_orgs:
        config_lis = []
        config_org = data_org['conf_txt']
        
        config_lis_x = config_org.split('\n')
        while '' in config_lis_x:
            config_lis_x.remove('')
        for x in config_lis_x:
            s = x.strip()
            config_lis.append(s)
        dev_dic['IPAddrArr'] = data_org['fw_ip']
        dev_dic['commandArr'] = config_lis
        datas_to_dev.append(dev_dic)
    jobNamejoy = random.randint(1,10000)
     
    try:
        cmcs = CMCS(str(jobNamejoy),datas_to_dev)
        #cmcs = CMCS(str(jobNamejoy),[{'IPAddrArr':['11.12.68.104'],'commandArr':['show int bri','show inr']}])
        ##print(cmsc_xml.get_report('_Chasis_Description_Line-Card_Info_Report'))
        test = cmcs.push_to_cmcs()
        print test
    except Exception as e:
        print(e)
    """
    try:
        cmcs = CMCS('jobNameyioy',[{'IPAddrArr':['11.12.68.104'],'commandArr':['show int bri','show inr']}])
        ##print(cmsc_xml.get_report('_Chasis_Description_Line-Card_Info_Report'))
        cmcs.push_to_cmcs()
        print('okkkk')
    except Exception as e:
        print(e)
        pass
    """
