# -*- coding: utf-8 -*-

{
    "name": "Metalesa - Purchase Order Mail From Contact",
    "version": "12.0.0.2",
    "author": "Visiion - Praxya",
    "summary": "Specifies when a partner has the quality email",
    "license": "AGPL-3",
    "category": 'Purchase',
    'website': 'www.praxya.com',
    'depends': [
        'purchase',
        'purchase_order_line_view',
    ],
    'data': [
        'views/purchase_order_view.xml',
        'views/res_partner_view.xml',
    ],
    'auto_install': True,
}
