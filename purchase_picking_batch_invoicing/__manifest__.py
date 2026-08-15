# -*- coding: utf-8 -*-

{
    "name": "Metalesa - Purchase Picking Batch Invoicing",
    "summary": "Create vendor bills from selected purchase receipts",
    "version": "12.0.1.0.6",
    "author": "TEPUI DEV SOLUCIONES S.L.",
    "license": "AGPL-3",
    "category": "Purchases",
    "depends": [
        "purchase_stock",
        "purchase_secondary_unit",
        "account_invoice_secondary_values",
        "stock_picking_transport",
    ],
    "data": [
        "wizard/purchase_picking_invoice_wizard_views.xml",
        "views/stock_picking_views.xml",
        "views/account_invoice_views.xml",
    ],
    "installable": True,
}
