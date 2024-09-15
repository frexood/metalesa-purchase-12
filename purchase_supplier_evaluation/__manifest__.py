# -*- coding: utf-8 -*-
{
    "name": "Metalesa - Purchase Supplier Evaluation",
    "version": "12.0.0.3",
    "author": "Praxya",
    "summary": "Add calification to the supplier based in information",
    "license": "AGPL-3",
    "category": 'Purchase',
    'website': 'www.praxya.com',
    'depends': [
        'purchase',
        'purchase_order_mail_from_contact',
        'mgmtsystem_nonconformity',
        'account'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_view.xml'
    ],
    'auto_install': True,
}
