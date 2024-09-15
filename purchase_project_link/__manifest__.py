# -*- coding: utf-8 -*-

{
    "name": "Metalesa - Purchase Project Link",
    "version": "12.0.0.3",
    "author": "Alejandro Granados <agranados@praxya.com>",
    "summary": "Add a button to view purchase related with project in projects view",
    "license": "AGPL-3",
    "category": 'Purchase',
    'website': 'www.praxya.com',
    'depends': [
        'purchase_analytic',
        'stock_picking_analytic',
        'purchase_order_line_view',
        'meta_analytic_cost',
    ],
    'data': [
        'views/project_project_view.xml'
    ],
    'auto_install': True,
}
