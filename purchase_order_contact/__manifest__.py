# -*- encoding: utf-8 -*-
##############################################################################
#
#    Module Writen to OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Obertix Free Solutions (<http://obertix.net>).
#                       cubells <info@obertix.net>
#                       Alejandro Granados <agranados@praxya.com> (Migration 8 - 12)
#
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
##############################################################################

{
    'name': 'Metalesa - Purchase Order Contact',
    'version': '1.2',
    'summary': """ Add a contact to the purchase order. The contact
                   has to be a contact of the partner of the order """,
    'author': 'Cubells <info@obertix.net> - Alejandro Granados <agranados@praxya.com> (Migration 8 - 12)',
    'website': 'http://www.puntsistemes.es',
    'license': 'AGPL-3',
    'category': 'Purchase',
    'depends': [
        'purchase'
    ],
    'data': [
        'views/purchase_order.xml'
    ],
    'auto_install': True,
}
