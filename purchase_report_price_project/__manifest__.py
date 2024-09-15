# -*- coding: utf-8 -*-

{
    "name": "Metalesa - Purchase Report Price Project",
    "version": "12.0.0.1",
    "author": "Praxya",
    "summary": "Add price unit, standard price and related project to analytics of purchase",
    "license": "AGPL-3",
    "category": 'Purchase',
    'website': 'www.praxya.com',
    'depends': [
        'purchase',
        'project',
        'stock',
        'purchase_analytic'
    ],
    'data': [
        'report/purchase_report_view.xml'
    ],
    'auto_install': True,
}
