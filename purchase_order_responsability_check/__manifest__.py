# -*- coding: utf-8 -*-
# (c) 2020 Praxya - Miquel March <mmarch@praxya.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Metalesa - Purchase Order Responsability Check",
    "version": "0.1",
    "author": "Praxya",
    "summary": "Check de responsabilidad al confirmar compras",
    "license": "AGPL-3",
    "category": 'Purchase',
    'website': 'www.praxya.com',
    'depends': [
        'purchase',
    ],
    'data': [
        'views/purchase_view.xml',
        'wizard/views/purchase_order_responsability_form.xml',
    ],
}
