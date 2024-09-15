# -*- coding: utf-8 -*-
{
    "name": "Metalesa - Purchase Receibe Products View",
    "version": "12.0.0.1",
    "author": "Praxya, Jaime Valero",
    "summary": """Add supplier to the moves and groupings
                about supplier and analytic account""",
    "license": "AGPL-3",
    "category": 'Purchase',
    'website': 'www.praxya.com',
    'depends': [
        'stock',
        'purchase',
        'stock_picking_analytic'
    ],
    'data': [
        'views/stock_move.xml'
    ],
    'auto_install': True,
}
