# -*- coding: utf-8 -*-

{
    "name": "Metalesa - Purchase Order Tree Color Status",
    "summary": "Changes color lines depending on picking state",
    "version": "12.0.0.1",
    "author": "Praxya, " "Jaime Valero",
    "license": "AGPL-3",
    "category": 'Purchase',
    'website': 'www.praxya.com',
    'depends': [
        'purchase',
        'purchase_picking_state',
    ],
    'data': [
        'views/purchase.xml'
    ],
    'auto_install': True,
}
