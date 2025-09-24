# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Restrict Zero Quantity',
    'version': '1.3',
    'summary': 'Restrict the zero quantity product in the sale order line, only show the ',
    'sequence': 10,
    'description': """
Restrict Zero Quantity
====================
Restrict the Zero Available Quantity Products are not show out in the Sale Order line it's useful to don't select the not available or zero quantity products  """,
    'category': 'Sale',
    'website': 'https://alantechnologies.in',
    'depends': ['base_setup', 'sale', 'sale_management','stock'],
    'data': [
        'views/sale_order_line.xml',
    ],

    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
