# -*- coding: utf-8 -*-

from odoo import models, fields, _


class PurchaseOrderLine(models.Model):
    _name = 'purchase.order.line'
    _inherit = ['purchase.order.line', 'mail.thread']

    partner_id_rel = fields.Many2one(
        comodel_name='res.partner',
        related='order_id.partner_id',
        string='Proveedor'
    )

    email_id_rel = fields.Char(
        related='order_id.partner_id.email',
        string=_('Email')
    )

    product_attribute_value_rel = fields.Many2many(
        related='product_id.attribute_value_ids',
        string='Valor de atributo',
    )
