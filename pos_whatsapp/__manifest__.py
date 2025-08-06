# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by CandidRoot Solutions Pvt. Ltd.
# See LICENSE file for full copyright and licensing details.

{
    "name": "Pos Auto Send Whatsapp",
    "version": "18.0.0.1",
    'author': "CandidRoot Solutions Pvt. Ltd.",
    'website': 'https://www.candidroot.com/',
    'category': 'Point of Sale',
    'description': """ This module allows to send Whatsapp when validating PoS order.""",
    "depends": ['point_of_sale',],
    'data': [
        'views/pos_config.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
             'pos_whatsapp/static//src/js/receipt_screen.js',
            'pos_whatsapp/static/xml/receipt_screen.xml',

        ],
    },
    'images': ['static/description/banner.png'],
    'live_test_url': 'https://youtu.be/vX_qoSM5vOw',
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
