{
    'name': 'Custom Invoice Report 80 mm',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'Custom invoice report with outstanding credits  amount and Post Dated  cheques amount',
    'description': 'This module customizes the invoice report to include outstanding credits amount  and post-dated cheques amount .The Invoice PDF report is 80mm',
    'sequence': 1,
    'author': 'Alan Technologies',
    'company': 'Alan Technologies',
    'maintainer': 'Alan Technologies',
    'website': "https://alantechnologies.in/",
    'depends': ['account', 'base'],
    'data': [
        'models/model_fields.xml',
        'views/report_view.xml',
        'actions/report_action.xml',

    ],
    'images': ['static/description/banner.gif'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
