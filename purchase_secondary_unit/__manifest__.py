# -*- coding: utf-8 -*-

{
    "name": "Metalesa - Purchase Secondary Unit",
    "version": "12.0.0.5",
    "summary": "Adds second unit of purchase on products",
    "author": "Praxya",
    "license": "AGPL-3",
    "category": 'Purchase',
    'website': 'www.praxya.com',
    'depends': [
        'purchase',
        'stock',
        'purchase_order_certifications',
        'account'
    ],
    'data': [
        # 'data/dp_data.xml',
        'data/purchase_order_server_action.xml',
        'views/purchase_order_view.xml',
        'views/product_view.xml',
    ],
}
