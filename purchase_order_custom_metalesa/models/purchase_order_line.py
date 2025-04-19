# -*- coding: utf-8 -*-

from odoo import fields, models, api


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    where_to_store = fields.Selection([
        ('inside', 'DENTRO'),
        ('doesnot_matter', 'DA IGUAL'),
        ('doesnot_apply', 'NO APLICA'),
    ], string="Dónde almacenar", requered=True)
