# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Metalesa - Purchase order line price history",
    "version": "12.0.1.0.0",
    "category": "Purchases Management",
    "summary": "Add product price history in puchase orders",
    "author": "Praxya, "
              "Jaime Valero",
    "website": "https://www.praxya.com",
    "license": "AGPL-3",
    "depends": [
        "purchase",
    ],
    "data": [
        "wizards/purchase_order_line_price_history.xml",
        "views/purchase_views.xml",
    ],
    "installable": True,
    'auto_install': True,
}
