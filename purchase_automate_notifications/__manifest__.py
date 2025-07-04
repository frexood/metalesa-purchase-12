# -*- coding: utf-8 -*-
{
    'name': 'Automatizar recepcion de compras ',
    'version': '12.0.1.0',
    'summary': """ Purchase_automate_notifications Summary """,
    'author': 'Metalesa',
    'website': 'www.metalesa.com',
    'category': 'Warehouse',
    'depends': ['base', 'stock','purchase','mail'],
    "data": [
        "data/mail_template.xml",
        "security/ir.model.access.csv",
        "views/purchase_notification_config_views.xml",
        "views/purchase_receive_notification_views.xml"
    ],
    
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
