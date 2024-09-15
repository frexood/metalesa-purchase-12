# -*- coding: utf-8 -*-# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.multi
    @api.depends('product_id')
    def _compute_product_uop_coeff(self):
        for record_id in self:
            if record_id.product_id and record_id.product_uop == record_id.product_id.uop_id:
                record_id.product_uop_coeff = record_id.product_id.uop_coeff
            else:
                record_id.product_uop_coeff = 1.0

    product_uop_qty = fields.Float(
        string=_('Quantity (UoP)'),
        readonly=True,
        digits=dp.get_precision('Product UoP')
    )

    product_uop = fields.Many2one(
        comodel_name='uom.uom',
        string=_('Product UoP')
    )

    product_uop_coeff = fields.Float(
        comodel_name='uom.uom',
        string=_('UoM -> UoP Coeff'),
        digits=dp.get_precision('Product UoP'),
        compute=_compute_product_uop_coeff
    )

    price_unit_uop = fields.Float(
        string=_('UoP Unit Price'),
        readonly=True,
        digits=dp.get_precision('Product Price')
    )

    @api.onchange('price_unit')
    def onchange_price_unit(self):
        if self.product_id:
            self.price_unit_uop = self.price_unit / self.product_id.uop_coeff

    @api.onchange('price_unit_uop')
    def onchange_price_unit_uop(self):
        if self.product_id:
            self.price_unit = self.price_unit_uop * self.product_id.uop_coeff

    @api.onchange('product_uop_qty')
    def onchange_product_uop_qty(self):
        if self.product_id:
            self.product_qty = self.product_uop_qty / self.product_id.uop_coeff

    @api.onchange('product_qty')
    def onchange_product_qty(self):
        if self.product_id:
            self.product_uop_qty = self.product_qty * self.product_id.uop_coeff

    @api.onchange('product_uop')
    def onchange_product_uop(self):
        if self.product_uop == self.product_id.uop_id:
            self.product_uop_coeff = self.product_id.uop_coeff
        else:
            self.product_uop_coeff = 1.0

    @api.onchange('product_id')
    def onchange_product_id(self):
        res = super(PurchaseOrderLine, self).onchange_product_id()

        if bool(self.product_id):
            self.product_uom = self.product_id.uom_id.id
            self.product_uop = self.product_id.uom_po_id.id or self.product_id.uop_id.id
            self.name = self.product_id.description_purchase_product or ''
        else:
            self.product_uom = False
            self.product_uop = False
        return res

#
# class AccountInvoice(models.Model):
#     _inherit = 'account.invoice'
#
#     @api.multi
#     def action_invoice_re_open(self):
#         pedidos = self.env['purchase.order'].search([])
#         for pedido in pedidos:
#             for linea in pedido.order_line:
#                 vals = self.write({'purchase_unit_uop': linea.price_unit,
#                                    'product_uop': linea.product_uom,
#                                    'product_uop_qty': linea.product_qty
#                                })
#
#         return vals