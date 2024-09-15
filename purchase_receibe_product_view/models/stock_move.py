# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.depends('purchase_line_id')
    @api.multi
    def _compute_supplier_id(self):
        for i in self:
            if i.purchase_line_id:
                i.supplier_id = i.purchase_line_id.order_id.partner_id

    supplier_id = fields.Many2one(
        comodel_name='res.partner',
        compute=_compute_supplier_id,
        string=_('Supplier'),
        store=True
    )

    atributos_ids = fields.Many2many('product.attribute.value', related='product_id.attribute_value_ids', string=_('Valor de atributo'))
