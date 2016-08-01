# -*- coding: utf-8 -*-
##############################################################################
#
#    Change automatic
#    Copyright (C) 2016-2017 Nantian.
#
#
#
##############################################################################
from openerp import models , fields, api,exceptions
import re,base64
from IPy import IP
import json,sys
import  urllib2 
import requests
import cookielib
from urllib import urlencode
import os
from excel_import import  Read_Excel

from cmcs_service import CMCS
import random


# 需求表
class Order(models.Model):
    _name = 'automatic.order'
    _rec_name = 'order_id'

    order_id = fields.Char(required=True)  # 工单号
    line_ids = fields.One2many('automatic.order_line','order_id')
    err_log = fields.Text()  # 需求表检查错误日志
    format_log = fields.Text()  # 需求表地址自动优化日志
    compliance_log = fields.Text()  # 需求表地址合规检查日志
    aclresult_ids = fields.One2many('automatic.aclresult','order_id')
    # order_no = fields.Integer()  # 工单具体行号
    isok = fields.Boolean(default=True)  # 需求表检查是否正常
    compliance = fields.Boolean(default=True)  # 需求表合规效验是否正常
    # protocol = fields.Char()  # 协议名称（ip/tcp/udp）三类
    # sourse_name = fields.Char()  # 源地址描述
    # sourse_str = fields.Char()  # 源地址原始信息
    # sourse_obj = fields.Char()  # 源地址格式化后数组，单位格式为（ip，掩码）
    # dst_name = fields.Char()  # 目的地址描述
    # dst_str = fields.Char()  # 目的地址原始信息
    # dst_obj = fields.Char()  # 目的地址格式化后数组，单位格式为（ip，掩码）
    # server_name = fields.Char()  # 应用名称
    # server_str = fields.Char()  # 目标端口原始信息
    # server_obj = fields.Char()  # 目标端口格式化后数组，单位为（起始端口，结束端口）
    #script_id = fields.Many2one('automatic.conftxt')    # 关联自动生产的脚步,外键关联脚步表
    device_ids = fields.Many2many('automatic.device')

    state = fields.Selection([
        ('new' , u'新建需求') ,
        ('Format Check' , u'格式检查') ,
        ('Rule Check' , u'合规检查') ,
        ('Script Check' , u'脚本检查') ,
        ('Exec' , u'脚本执行') ,
        ('Verification' , u'执行校验') ,
        ('Closed' , u'已关闭') ,
    ] , default='new' , string="状态" , ack_visibility='onchange')
    result = fields.Selection([
        ('success' , u'成功') ,
        ('ruleCheck_fault' , u'合规检查失败') ,
        ('scriptCheck_fault' , u'脚本检查失败') ,
        ('exec_fault' , u'脚本执行失败') ,
        ('exec_ok',u'脚本执行成功'),
        ('verification_fault' , u'执行校验失败') ,
        ('ongoing' , u'进行中') ,
    ] , default='ongoing' , string="结果")
    data = fields.Binary('lines')
    # api for 中行程序
    cj = cookielib.CookieJar()
    cookie_support = urllib2.HTTPCookieProcessor(cj)
    opener = urllib2.build_opener(cookie_support, urllib2.HTTPHandler)
    urllib2.install_opener(opener)
    def getdata_from_res(self,data_url):
        #抓取数据请求
        #DataRequest = urllib2.Request(data_url)
        #DataResponse = urllib2.urlopen(DataRequest).read()
        data = requests.post(data_url)
        return data.text


    def postdata_to_res(self,dataurl,args):
        postdata = json.dumps(args)
        headers = {'Accept-Encoding' :'gzip,default','Content-Type':'application/json',}

        LoginRequest = urllib2.Request(dataurl, data=postdata, headers=headers)
        LoginResponse = urllib2.urlopen(LoginRequest)
        if LoginResponse.getcode() == 200:
            return LoginResponse.read()
        else:
            return 0
    def analytic_rule(self,data):
        my = json.loads(data)
        for datw in my:
            record ={}
            record1={}
            for k, v in datw.iteritems():
                if k == "find_acl" and v:
                    for shuju in datw['find_acl']:
                        for k2, v2 in shuju.iteritems():
                            v0 = ''
                            if k2 == "match_srt":
                                for v1 in v2:
                                    v0 = v1[0] + r'/' + v1[1]
                                record1['match_srt']=v0
                                print k2, ':', v0
                            elif k2 == "match_dst":
                                for v1 in v2:
                                    v0 = v1[0] + r'/' + v1[1]
                                record1['match_dst']=v0
                            elif k2 == "match_ser":
                                for v1 in v2:
                                    if not v0:
                                        v0 = str(v1[0]) + r',' + str(v1[1])
                                    elif v0:
                                        v0 = v0 + ',' + str(v1[0]) + r',' + str(v1[1])
                                record1['match_ser']=v0
                                print k2, ':', v0
                            elif k2 == "acl_txt":
                                record1['acl_txt']=v2
                                print k2, ':', v2
                            elif k2 == "permit":
                                record1['permit']=v2
                            elif k2 == "acl_no":
                                record1['acl_no']=v2
                    if record1['permit']:
                          find = self.env['automatic.find_acl'].create(
                                {'acl_no': int(record1['acl_no']), 'acl_txt': record1['acl_txt'], 'match_dst': record1['match_dst'],
                                 'match_ser': record1['match_ser'], 'match_srt': record1['match_srt'] , 'permit':1})
                    else:
                         find = self.env['automatic.find_acl'].create(
                                {'acl_no': int(record1['acl_no']), 'acl_txt': record1['acl_txt'], 'match_dst': record1['match_dst'],
                                 'match_ser': record1['match_ser'], 'match_srt': record1['match_srt'], 'permit': 0})
                v0 = ''
                if k == "server_obj":
                    for v1 in v:
                        if not v0:
                            v0 = str(v1[0]) + r',' + str(v1[1])
                        elif v0:
                            v0 = v0 + ',' + str(v1[0]) + r',' + str(v1[1])
                    record['server_obj']=v0
                elif k == "dst_obj":
                    for v1 in v:
                        v0 = v1[0] + r'/' + v1[1]
                        record['dst_obj']=v0
                elif k == "sourse_obj":
                    for v1 in v:
                        v0 = v1[0] + r'/' + v1[1]
                        record['sourse_obj']=v0
                elif k=="find_acl":
                    pass
            
            record['order_id'] = self.env['automatic.order'].search([('order_id', '=', datw['order_id'])], limit=1).id
            record['order_line_id'] = self.env['automatic.order_line'].search([('order_id.order_id', '=', datw['order_id']),('line_no', '=', datw['order_no'])], limit=1).id
            if datw['find_acl']:
                self.env['automatic.aclresult'].create(
                        {'server_obj': record['server_obj'], 'protocol': datw['protocol'], 'order_line_id': record['order_line_id'],
                         'acl_name': datw['acl_name'], 'isfind': datw['isfind'], 'order_id': record['order_id'], 'dst_obj': record['dst_obj'],
                         'sourse_obj': record['sourse_obj'], 'fw_ip': datw['fw_ip'],'same_sourse_name':datw['same_sourse_name'],
                         'same_server_name':datw['same_server_name'],'same_dst_name':datw['same_dst_name'],'rest_sourse':datw['rest_sourse'],'find_acl': find.id})
            if not datw['find_acl']:
                    self.env['automatic.aclresult'].create(
                        {'server_obj': record['server_obj'], 'protocol': datw['protocol'], 'order_line_id': record['order_line_id'],
                         'acl_name': datw['acl_name'], 'isfind': datw['isfind'], 'order_id': record['order_id'], 'dst_obj': record['dst_obj'],
                         'sourse_obj': record['sourse_obj'], 'fw_ip': datw['fw_ip'],'same_sourse_name':datw['same_sourse_name'],
                         'same_server_name':datw['same_server_name'],'same_dst_name':datw['same_dst_name'],'rest_sourse':datw['rest_sourse'],})  
    def analytic_config(self,data):
        my = json.loads(data)
        for datw in my:
            if datw:
                order_line_id = self.env['automatic.order_line'].search([('order_id.order_id', '=',datw['order_id']),('line_no', '=', datw['order_no'])], limit=1).id
                device_id = self.env['automatic.device'].search([('ip', '=',datw['fw_ip'])],limit=1).id
                self.env['automatic.conftxt'].create({'conf_txt':datw['conf_txt'],'fw_ip':datw['fw_ip'],'date_modified':datw['date_modified'],'order_line_id':order_line_id,'device_id':device_id})
    def action_new (self):
        if self.state != 'new':
            self.err_log=''
            self.format_log=''
            self.compliance_log=''

        self.state = 'new'

    def action_formatCheck(self):
        if self.state != 'Format Check':
            for line_ids in self.line_ids:
                for aclresult_ids in line_ids.aclresult_ids:
                    if aclresult_ids:
                        aclresult_ids.find_acl.unlink()
                        aclresult_ids.unlink()
            
        self.state = 'Format Check'
        err_logs=''
        format_logs=''
        compliance_logs=''

        #把生产的需求单信息按行发给中行服务端
        for id in self.line_ids:
            data = {
                    "order_id": id.order_id.order_id,
                    "order_no": id.line_no,
                    "protocol": id.protocol,
                    "sourse_name": id.sourse_name,
                    "sourse_str": id.sourse_str,
                    "dst_name": id.dst_name,
                    "dst_str": id.dst_str,
                    "server_name": id.server_name,
                    "server_str": id.server_str,
                }
            return_line = self.postdata_to_res('http://22.1.111.29:5000/order',data)
            if return_line:
                returns=json.loads(return_line)
                if returns['compliance']:
                    id.compliance=1
                else:
                    id.compliance=0
                if returns['isok']:
                    id.isok=1
                else:
                    id.isok=0
                if returns['err_log']:
                    for err_log in returns['err_log']:
                        err_logs += err_log
                        err_lods += os.linesep 
                    self.err_log=err_logs
                if returns['format_log']:
                    for format_log in returns['format_log']:
                        format_logs += format_log
                        format_logs += os.linesep
                    self.format_log=format_logs
                if returns['compliance_log']:
                    for compliance_log in returns['compliance_log']:
                        compliance_logs += compliance_log
                        compliance_logs += os.linesep
                    self.compliance_log=compliance_logs


    def action_ruleCheck(self):
        if self.state != 'Rule Check':
            for line_ids in self.line_ids:
                for conftxt_ids in line_ids.conftxt_ids:
                    if conftxt_ids:
                        conftxt_ids.unlink()
        self.state = 'Rule Check'
        data=self.getdata_from_res('http://22.1.111.29:5000/find/'+self.order_id)
        self.analytic_rule(data)
    def action_scriptCheck(self):
        self.state = 'Script Check'
        data=self.getdata_from_res('http://22.1.111.29:5000/config/'+self.order_id)
        self.analytic_config(data)
    def action_exec(self):
        self.state = 'Exec'
        data=self.getdata_from_res('http://22.1.111.29:5000/config/'+self.order_id)
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
        print datas_to_dev
        jobNamejoy = random.randint(1,10000)
         
        try:
            cmcs = CMCS(str(jobNamejoy),datas_to_dev)
            #cmcs = CMCS(str(jobNamejoy),[{'IPAddrArr':['11.12.68.104'],'commandArr':['show int bri','show inr']}])
            ##print(cmsc_xml.get_report('_Chasis_Description_Line-Card_Info_Report'))
            test = cmcs.push_to_cmcs()
            self.err_log = test
        except Exception as e:
            print(e)
            self.err_log = str(e) + '\n' + str(datas_to_dev) + '\n' + str(jobNamejoy)
    


    def action_verification(self):
        self.state = 'Verification'
    def action_closed(self):
        self.state = 'Closed'
    '''
    def import_order_line(self, cr, uid, ids, context):
        for wiz in self.browse(cr, uid, ids):
            if not wiz.data:
                raise exceptions.ValidationError('请选择要导入的文件')
        r = Read_Excel(file_contents=base64.decodestring(wiz.data))
        trades = r()[:]
        print '=' * 80
        if not len(trades):
            raise exceptions.ValidationError('转下一步前，请填写处理过程及记录')
        for line in r():
            line['order_id'] = ids[0]
            print line
            self.pool.get('automatic.order_line').create(cr, uid, line, context)
            # self.env['automatic.order_line'].create(line)

    '''
    @api.multi
    def import_order_line(self):
        print 'aaaa'*10

        print type(self)
        wiz=self.browse(self.id)
        print wiz
        if not wiz.data:
            raise exceptions.ValidationError('请选择要导入的文件')
        r = Read_Excel(file_contents=base64.decodestring(wiz.data))
        trades = r()[:]
        print '=' * 80
        print len(trades)
        if not len(trades):
            raise exceptions.ValidationError('转下一步前，请填写处理过程及记录')
        for line in r():
            line['order_id'] = self.id
            self.env['automatic.order_line'].create(line)



class Order_line(models.Model):
    _name = 'automatic.order_line'
    _rec_name = 'line_no'

    line_no = fields.Integer()  # 工单具体行号
    isok = fields.Boolean(default=True)  # 需求表检查是否正常
    compliance = fields.Boolean(default=True)  # 需求表合规效验是否正常
    protocol = fields.Text()  # 协议名称（ip/tcp/udp）三类
    sourse_name = fields.Char()  # 源地址描述
    sourse_str = fields.Text()  # 源地址原始信息
    sourse_obj = fields.Char()  # 源地址格式化后数组，单位格式为（ip，掩码）
    dst_name = fields.Char()  # 目的地址描述
    dst_str = fields.Text()  # 目的地址原始信息
    dst_obj = fields.Char()  # 目的地址格式化后数组，单位格式为（ip，掩码）
    server_name = fields.Char()  # 应用名称
    server_str = fields.Text()  # 目标端口原始信息
    server_obj = fields.Char()  # 目标端口格式化后数组，单位为（起始端口，结束端口）
    order_id = fields.Many2one('automatic.order')
    device_ids = fields.Many2many('automatic.device')
    conftxt_ids = fields.One2many('automatic.conftxt','order_line_id')
    aclresult_ids = fields.One2many('automatic.aclresult','order_line_id')

    def pop_window(self, cr, uid, ids, context=None):
        mod_obj = self.pool.get('ir.model.data')
        form_res = mod_obj.get_object_reference(cr, uid, 'change_automatic', 'automatic_conftxt_tree_view')
        form_id = form_res and form_res[1] or False
        value = {
            'name':('Name'),
            'res_model': 'automatic.conftxt',
            'views': [[False, 'tree']],
            'type': 'ir.actions.act_window',
            'target': 'new',
            "domain": [["order_line_id", "=", ids]],
        }
        return value

    def button_event(self, cr, uid, ids, *args):
        return self.pop_window(cr, uid, ids, None)

# 地址组表
class Network(models.Model):
    _name = 'automatic.network'
    _rec_name = 'net_name'

    fw_ip = fields.Char()  # 防火墙地址
    net_name = fields.Char()  # 地址组名称
    obj_items = fields.Char()  # 地址组列表，单位格式为（ip，掩码）
    device_id = fields.Many2one('automatic.device')  # 关联的设备,外键关联设备表


# 路由表
class Route(models.Model):
    _name = 'automatic.route'

    src = fields.Char()     # 源地址
    dst = fields.Char()     # 目的地址
    mask = fields.Char()    # 子网掩码
    interface = fields.Char()   # 路由接口
    nexthop = fields.Char()     # 路由下一跳
    device_id = fields.Many2one('automatic.device')  # 关联的设备,外键关联设备表
    @api.multi
    def test(self):
        sebei='YQBWZ-APP-FW4'
        sebei1=self.env['automatic.device'].search([('name', '=',sebei)], limit=1)
        log = open(r"C:/Users/nantian/Desktop/log/YQBWZ-APP-FW4.log")
        file = log.read()
        relog = re.compile(r"sh route(.*?)\#", re.DOTALL)
        result = relog.search(file)
        mores = result.group(1).split("\n")

        for more in mores:
            record = []
            if more.find(r".") >= 0:
                if more.find(r",") >= 0:
                    print more
                    shujus = more.split(r",")
                    if len(shujus) == 2:
                        shujus[1] = "".join(shujus[1].split())
                        record.append(shujus[1])
                        ips = shujus[0].split(r" ")
                        for ip in ips:
                            if ip.find(r".") >= 0:
                                record.append(ip)
                        for rec in record:
                            print rec
                        if len(record) == 4:
                            self.env['automatic.route'].create({'interface': record[0], 'dst': record[1], 'dst_mask': record[2], 'nexthop': record[3],'device_id': sebei1.id})
                        if len(record) == 3:
                            self.env['automatic.route'].create({'interface': record[0], 'dst': record[1], 'dst_mask': record[2],'device_id': sebei1.id})

        log.close()

    @api.multi
    def test1(self):
        shujus=self.env['automatic.route'].search([(1, '=', 1)])
        for shuju in shujus:
            if shuju.dst:
                ip=str(shuju.dst)+str('/')+str(shuju.dst_mask)
                print ip
                print IP(ip)
                print  IP('2.34.1.1/32') in IP(ip)


# 设备接口表
class Interfaces(models.Model):
    _name = 'automatic.interface'

    name = fields.Char()    # 接口名称
    ip = fields.Char()      # 接口地址
    mask = fields.Char()    # 接口掩码
    device_id = fields.Many2one('automatic.device')     # 关联的设备,外键关联设备表


# 服务端口组表
class Server(models.Model):
    _name = 'automatic.server'
    _rec_name = 'ser_name'

    fw_ip = fields.Char()  # 防火墙地址
    ser_name = fields.Char()  # 策略组名称
    obj_items = fields.Char()  # 端口组列表，单位格式为（起始端口，结束端口）
    device_id = fields.Many2one('automatic.device')  # 关联的设备,外键关联设备表


# 所有设备的ACL表
class Aclline(models.Model):
    _name = 'automatic.aclline'
    _rec_name = 'acl_name'

    fw_ip = fields.Char()  # 防火墙地址
    acl_name = fields.Char()  # 防火墙策略名称
    acl_permit = fields.Boolean(default=True)  # 策略permit为true，deny为false
    acl_no = fields.Integer()  # 策略行号
    protocol = fields.Char()  # 协议名称
    raw_data = fields.Char()  # 策略原始配置
    sourse_obj = fields.Many2one('automatic.network')  # 源地址组，外键关联对应地址组对象
    dst_obj = fields.Many2one('automatic.network')  # 目的地址组，外键关联对应地址组对象
    server_obj = fields.Many2one('automatic.server')  # 服务端口组，外键关联对应策略组对象
    device_id = fields.Many2one('automatic.device')  # 关联设备,外键关联设备表
    sourse_obj1 = fields.Char() # 源地址
    dst_obj1 = fields.Char() # 目的地址
    server_obj1 = fields.Char() # 服务端口组
    @api.multi
    def test(self):
        sebei='YQBWZ-APP-FW3'
        sebei1=self.env['automatic.device'].search([('name', '=',sebei)], limit=1)
        log = open(r"F:/test/log/YQBWZ-APP-FW3.log")
        file = log.read()
        relog = re.compile(r"sh access-list(.*?)\#", re.DOTALL)
        result = relog.search(file)
        mores = result.group(1).split("\n")

        for more in mores:
            if more.find(r"extended") >= 0:
                shujus1 = more.split(r"extended")
                shujus = shujus1[1].split(r"(")[0]
                shujuss = shujus.split(r' ')
                i = 0
                for shuju in shujuss:
                    if shuju == 'host':
                        shujuss[i + 1] += r'/32'
                        #不需要数据设空值
                        shujuss[i] = ''
                    elif shuju.find(r"255.") >= 0:
                        shujuss[i - 1] += r'/' + shuju
                        #转换格式为127.0.0.0/24
                        shujuss[i - 1] = IP(shujuss[i - 1]).strNormal(1)
                        #设空值
                        shujuss[i] = ''
                    elif shuju == 'object-group':
                        # 设空值
                        shujuss[i] = ''
                    elif shuju == 'range':
                        shujuss[i + 1] += r'-' + shujuss[i + 2]
                        # 设空值
                        shujuss[i] = ''
                        shujuss[i + 2] = ''
                    elif shuju == 'eq':
                        # 设空值
                        shujuss[i] = ''
                    elif shuju == 'log' or shuju == 'disable' or shuju.find(r'0x') >= 0:
                        # 设空值
                        shujuss[i] = ''

                    if i == len(shujuss) - 1:
                        break
                    i = i + 1

                #数据加入列表
                record = []
                for shuju1 in shujuss:
                    if shuju1:
                        record.append(shuju1)
                #含有服务端口
                if len(record) == 5:
                    if record[0] =="permit":
                        self.env['automatic.aclline'].create({'acl_permit': 1, 'protocol': record[1], 'sourse_obj1': record[2], 'dst_obj1': record[3],'server_obj1':record[4],'device_id': sebei1.id})
                    elif record[0] =="deny":
                        self.env['automatic.aclline'].create({'acl_permit': 0, 'protocol': record[1], 'sourse_obj1': record[2], 'dst_obj1': record[3],'server_obj1':record[4],'device_id': sebei1.id})
                #不含服务端口
                if len(record) == 4:
                    if record[0] =="permit":
                        self.env['automatic.aclline'].create({'acl_permit': 1, 'protocol': record[1], 'sourse_obj1': record[2], 'dst_obj1': record[3],'device_id': sebei1.id})
                    elif record[0] =="deny":
                        self.env['automatic.aclline'].create({'acl_permit': 0, 'protocol': record[1], 'sourse_obj1': record[2], 'dst_obj1': record[3],'device_id': sebei1.id})


# ACL查询结果
class AclResult(models.Model):
    _name = 'automatic.aclresult'
    _rec_name = 'order_id'

    order_id = fields.Many2one('automatic.order',required=True)  # 工单号
    order_line_id = fields.Many2one('automatic.order_line')  # 工单具体行号
    fw_ip = fields.Char()  # 防火墙地址
    acl_name = fields.Char()  # 防火墙策略名称
    isfind = fields.Boolean(default=True)  # 是否查询到匹配策略
    deny_no = fields.Integer(default=0)  # deny的策略行号，无deny匹配则为0
    protocol = fields.Char()  # 协议名称
    sourse_obj = fields.Char()  # 查询的源地址组，单位格式为（ip，掩码）
    dst_obj = fields.Char()  # 查询的目的地址组，单位格式为（ip，掩码）
    server_obj = fields.Char()  # 查询的端口组，单位格式为（起始端口，结束端口）
    rest_sourse = fields.Char()  # 未放开的源地址组，单位格式为（ip，掩码）
    same_sourse_name = fields.Char()  # 已放开的源地址组名称
    same_dst_name = fields.Char()  # 已放开的目的地址组名称
    same_server_name = fields.Char()  # 已放开的端口组名称
    # find_acl为查询结果，单位内格式为（是否permit, 匹配的源地址组，策略行号，具体策略）
    find_acl = fields.Many2one('automatic.find_acl')
    @api.multi
    def test(self):
        data = '''[
  {
    "acl_name": "TESTFW-INSIDE-IN",
    "dst_obj": [
      [
        "10.1.75.93",
        "32"
      ]
    ],
    "find_acl": [
      {
        "acl_no": 7,
        "acl_txt": "access-list TESTFW-INSIDE-IN extended permit ip any any",
        "match_dst": [
          [
            "10.1.75.93",
            "32"
          ]
        ],
        "match_ser": [
          [
            137,
            137
          ],
          [
            138,
            138
          ]
        ],
        "match_srt": [
          [
            "10.13.25.72",
            "31"
          ]
        ],
        "permit": true
      }
    ],
    "fw_ip": "10.13.252.1",
    "isfind": true,
    "order_id": "TEST01",
    "order_no": 5,
    "protocol": "tcp",
    "server_obj": [
      [
        137,
        137
      ],
      [
        138,
        138
      ]
    ],
    "sourse_obj": [
      [
        "10.13.25.72",
        "31"
      ]
    ]
  },
  {
    "acl_name": "not_find",
    "dst_obj": [
      [
        "10.14.65.128",
        "32"
      ]
    ],
    "find_acl": [],
    "fw_ip": "not_fw",
    "isfind": false,
    "order_id": "TEST01",
    "order_no": 6,
    "protocol": "ip",
    "server_obj": [
      [
        12000,
        12000
      ]
    ],
    "sourse_obj": [
      [
        "10.233.33.0",
        "24"
      ]
    ]
  }
]'''
        my = json.loads(data)
        for datw in my:
            record =[]
            record1=[]
            for k, v in datw.iteritems():
                if k == "find_acl" and v:
                    for shuju in datw['find_acl']:
                        for k2, v2 in shuju.iteritems():
                            v0 = ''
                            if k2 == "match_srt" or k2 == "match_dst":
                                for v1 in v2:
                                    v0 = v1[0] + r'/' + v1[1]
                                record1.append(v0)
                                print k2, ':', v0
                            elif k2 == "match_ser":
                                for v1 in v2:
                                    if not v0:
                                        v0 = str(v1[0]) + r',' + str(v1[1])
                                    elif v0:
                                        v0 = v0 + ',' + str(v1[0]) + r',' + str(v1[1])
                                record1.append(v0)
                                print k2, ':', v0
                            else:
                                record1.append(v2)
                                print k2, ':', v2
                    if record1[5]:
                          find = self.env['automatic.find_acl'].create(
                                {'acl_no': int(record1[3]), 'acl_txt': record1[0], 'match_dst': record1[4],
                                 'match_ser': record1[2], 'match_srt': record1[1] , 'permit':1})
                    else:
                         find = self.env['automatic.find_acl'].create(
                                {'acl_no': int(record1[3]), 'acl_txt': record1[0], 'match_dst': record1[4],
                                 'match_ser': record1[2], 'match_srt': record1[1], 'permit': 0})
                v0 = ''
                if k == "server_obj":
                    for v1 in v:
                        if not v0:
                            v0 = str(v1[0]) + r',' + str(v1[1])
                        elif v0:
                            v0 = v0 + ',' + str(v1[0]) + r',' + str(v1[1])
                    record.append(v0)
                    print k, ':', v0
                elif k == "dst_obj" or k == "sourse_obj":
                    for v1 in v:
                        v0 = v1[0] + r'/' + v1[1]
                        record.append(v0)
                        print k, ':', v0
                elif k=="find_acl":
                    pass
                else:
                    record.append(v)
                    print k, ':', v
            record[5] = self.env['automatic.order'].search([('order_id', '=', record[5])], limit=1).id
            record[2] = self.env['automatic.order_line'].search([('order_id.id', '=', record[5]),('line_no', '=', record[2])], limit=1).id
            if datw['find_acl']:
                self.env['automatic.aclresult'].create(
                        {'server_obj': record[0], 'protocol': record[1], 'order_line_id': record[2],
                         'acl_name': record[3], 'isfind': record[4], 'order_id': record[5], 'dst_obj': record[6],
                         'sourse_obj': record[7], 'fw_ip': record[8], 'find_acl': find.id})
            if not datw['find_acl']:
                    self.env['automatic.aclresult'].create(
                        {'server_obj': record[0], 'protocol': record[1], 'order_line_id': record[2],
                         'acl_name': record[3], 'isfind': record[4], 'order_id': record[5], 'dst_obj': record[6],
                         'sourse_obj': record[7], 'fw_ip': record[8]})  


# 自动生成的可执行脚本表
class Conftxt(models.Model):
    _name = 'automatic.conftxt'
    #_rec_name = 'order_id'

    #order_id = fields.Many2many(required=True)  # 工单号
    order_line_id = fields.Many2one('automatic.order_line')  # 工单具体行号
    state = fields.Integer(default=0)  # 配置状态（0待审核1已审核2已提交）
    fw_ip = fields.Char()  # 防火墙地址
    conf_txt = fields.Text()  # 具体配置
    #date_modified = fields.Datetime('Date')  # 更新时间
    date_modified = fields.Char('Date')  # 更新时间
    device_id = fields.Many2one('automatic.device')


# 设备管理表
class Device(models.Model):
    _name = 'automatic.device'

    name = fields.Char()  # 设备名称
    ip = fields.Char(required=True)  # 设备管理地址
    username = fields.Char()  # 登录用户名
    password = fields.Char()  # 用户名密码
    acl_items = fields.One2many('automatic.aclline' , 'device_id')  # 防火墙策略列表，外键关联对应策略行对象
    route_ids = fields.One2many('automatic.route','device_id')  # 路由组对象列表，单位格式为（端口名称，路由段，掩码）
    int_ids = fields.One2many('automatic.interface','device_id')  # 接口组对象列表，单位格式为（入向列表，出向列表，端口名称）
    network_items = fields.One2many('automatic.network' , 'device_id')  # 地址组对象列表，外键关联对应地址组对象
    server_items = fields.One2many('automatic.server' , 'device_id')  # 端口组对象列表，外键关联对应端口组对象
    date_modified = fields.Char()  # 更新时间
    connected = fields.Char(default='失败')   # 连通性
    order_line_ids = fields.Many2many('automatic.order_line')
    conftxt_ids = fields.One2many('automatic.conftxt','device_id')
    @api.multi
    def updata_date(self):
        data = requests.get('http://22.1.111.29:5000/firewall')
        datas = json.loads(data.text)
        for datw in datas:
            devices = self.env['automatic.device'].search([('name', '=', datw['fw_name'])])            
            if devices:
                devices.date_modified=datw['date_modified']
                devices.ip=datw['fw_ip']
            else:
                self.env['automatic.device'].create({'name':datw['fw_name'],'ip':datw['fw_ip'],'date_modified':datw['date_modified']})
# 所有配置项表
class Ci_all(models.Model):
    _name = 'automatic.ci_all'
    _inherit =  'ir.model.fields'



# 配置项变更记录表
class Change_log(models.Model):
    _name = 'automatic.change_log'

    fields_id = fields.One2many('automatic.ci_all','id')
    

# acl 查询检测结果
class find_acl(models.Model):
    _name = 'automatic.find_acl'
    _rec_name = 'acl_txt'
    acl_no = fields.Integer() #策略行号
    acl_txt = fields.Char() #策略内容
    match_dst = fields.Char() #匹配到的目的地址
    match_ser = fields.Char() #匹配到的端口
    match_srt = fields.Char() #匹配到的源地址
    permit = fields.Boolean() #是否permit, 匹配的源地址组，策略行号，具体策略
