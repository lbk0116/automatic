# -*- coding: utf-8 -*-
##############################################################################
#
#    Change automatic
#    Copyright (C) 2016-2017 Nantian.
#
#
#
##############################################################################
{
    'name' : 'Change Automatic',
    'version' : '0.1',
    'author' : 'Nantian',
    'category' : 'Automatic',
    'description' : """
Change Automatic.
====================================

Change Automatic module that covers:
--------------------------------------------
    * 变更需求分析
    * 变更设备脚本生成

支持的设备:
--------------------------------------------------
    * 防火墙

    """,
    'website': 'https://www.nantian.com.cn',
    'depends' : ['base','base_setup', ],
    'data': [
        'views/view.xml',
        'views/menu.xml',
        'views/automatic_link.xml',
        'data/order_workflow.xml',
        'security/ir.model.access.csv',
    ],
    'qweb' : [
        'static/xml/automatic.xml'
    ],
    'demo': [
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
