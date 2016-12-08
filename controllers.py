# -*- coding: utf-8 -*-
from openerp import http,exceptions
import xlrd
import re

class Files(http.Controller):
    @http.route('/import_order', type='http', auth='public', methods=['POST','FILES'])
    def order_import(self, **post):
        datas = post['excel']
        if datas:
            if re.match(r".*.xls.?",datas.filename):
                tmp = datas.stream.read()
                if tmp:
                    excel = xlrd.open_workbook(filename=datas.filename,file_contents=tmp)
                    sh = excel.sheets()[0]
                    nrows = sh.nrows
                    if nrows <= 3:
                        return '请检查excel信息(少于4行)'
                    order_keys = sh.row_values(0)
                    order_values = sh.row_values(1)
                    orders={}
                    for o in range(0,len(order_keys)-1):
                        if "order_id" in order_keys[o]:
                            orders["order_id"]=order_values[o]
                        elif "deparment" in order_keys[o]:
                            orders["deparment"]=order_values[o]
                        elif "proposer" in order_keys[o]:
                            orders["proposer"]=order_values[o]
                        elif "phone" in order_keys[o]:
                            orders["phone"] = order_values[o]
                    if orders:
                        order_id = http.request.env['automatic.order'].sudo().create(orders)
                        lines_keys = sh.row_values(2)
                        print lines_keys
                        lines={}
                        if lines_keys:
                            for i in range(0, len(lines_keys)):
                                if "line_no" in lines_keys[i]:
                                    lines[str(i)] = "line_no"
                                elif "line_info" in lines_keys[i]:
                                    lines[str(i)] = "line_info"
                                elif "sourse_name" in lines_keys[i]:
                                    lines[str(i)] = "sourse_name"
                                elif "sourse_str" in lines_keys[i]:
                                    lines[str(i)] = "sourse_str"
                                elif "dst_name" in lines_keys[i]:
                                    lines[str(i)] = "dst_name"
                                elif "dst_str" in lines_keys[i]:
                                    lines[str(i)] = "dst_str"
                                elif "server_name" in lines_keys[i]:
                                    lines[str(i)] = "server_name"
                                elif "protocol" in lines_keys[i]:
                                    lines[str(i)] = "protocol"
                                elif "server_str" in lines_keys[i]:
                                    lines[str(i)] = "server_str"
                                else:
                                    lines[str(i)] = ""

                            for v in range(3,sh.nrows):
                                line = {}
                                for i_num in range(0, len(lines_keys)):
                                    if lines[str(i_num)]:
                                        line[lines[str(i_num)]] = sh.row_values(v)[i_num]
                                if line:
                                    line['order_id'] = order_id.id
                                    http.request.env['automatic.order_line'].sudo().create(line)
                            return "导入成功"
                    else:
                        return "请检查excel信息"
            else:
                return '请选择excel导入'
        else:
            return '请选择要导入的文件'



