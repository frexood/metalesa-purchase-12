# -*- coding: utf-8 -*-
{
    "name": "Metalesa - Purchase Order Line Calendar",
    "version": "12.0.0.6",
    "author": "Praxya, Jaime Valero",
    "summary": "Add information about moves of purchase order in Inventory -> Operations",
    "license": "AGPL-3",
    "category": 'Purchase',
    'website': 'www.praxya.com',
    'depends': [
        'purchase',
        'purchase_order_line_view',
        'purchase_receibe_product_view',
        'mrp_galvanizado',
        'stock',
    ],
    'data': [
        'views/purchase.xml',
        'views/stock_move_view.xml',
    ],
    'auto_install': True,
}
