# -*- coding: utf-8 -*-
{
    'name': "Odoo QuickBooks Connector",
    'summary': """
                    The QuickBooks to Odoo Instant Sync module provides seamless, 
                    real-time synchronization between QuickBooks and Odoo, 
                    keeping your data accurate and consistent across both platforms.
                """,
    'description': """
                    QuickBooks to Odoo Instant Sync Operation allows you to sync customers, vendors, items, sales orders, 
                    purchase orders, invoices, bills, credit notes, refunds from QuickBooks to Odoo. 
                    Additionally, it supports syncing sales orders, purchase orders, customer invoices, vendor bills, 
                    customer credit notes, vendor refunds, customer payments, vendor payments, products, 
                    and contacts in invoices, bills, sales orders, and purchase orders from Odoo to QuickBooks. 
                    This module ensures your accounting and operational data are always up-to-date, reducing manual entry and minimizing errors.
                """,
    'author': "Techloyce",
    'website': "http://www.techloyce.com",
    'category': 'sale',
    'version': '17.0.0.2',
    'price': 499,
    'currency': 'USD',
    "license": "OPL-1",
    'depends': ['base','contacts','sale_management','account','purchase','hr_expense','stock','account_accountant'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/settings.xml',
        'data/data.xml'
    ],
    'images': [
        'static/description/banner.gif',
    ],
    'external_dependencies': {'python': ['xmltodict', 'suds-py3']},
}
