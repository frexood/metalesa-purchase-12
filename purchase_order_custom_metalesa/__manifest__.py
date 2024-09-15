# -*- coding: utf-8 -*-
# (c) 2020 Praxya - Miquel March <mmarch@praxya.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Metalesa - Purchase Order Custom",
    "version": "0.13",
    "author": "Praxya",
    "summary": "Personalizaciones de compras para Metalesa",
    "license": "AGPL-3",
    "category": 'Purchase',
    'website': 'www.praxya.com',
    'depends': [
        'hr',
        'purchase_analytic',
        'purchase_picking_state',
        'purchase_order_line_view',
        'purchase_batch_invoicing',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/menu_views.xml',
        'views/purchase_view.xml',
        'views/stock_move_view.xml',
    ],
    'auto_install': True,
}
