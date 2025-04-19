# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class WzPurchaseOrderWhereStore(models.TransientModel):
    _name = 'wz.purchase.order.where.store'
    _description = _('wizard purchase order donde almacenar')

    name = fields.Char(_('Name'))

    purchase_order_id = fields.Many2one('purchase.order', string='purchase_order')
    where_to_store = fields.Selection([
        ('inside', 'DENTRO'),
        ('doesnot_matter', 'DA IGUAL'),
        ('doesnot_apply', 'NO APLICA'),
    ], string="Dónde almacenar", required=True)
    po_where_store_line_ids = fields.One2many('wz.purchase.order.where.store.line', 'wz_po_where_store_id',
        string='Order Line')

    def assign_where_store_line(self):
        purchae_order_rec = self.env['purchase.order'].search([('id','=',self.purchase_order_id.id)])
        if purchae_order_rec:
            for ln_where_store in self.po_where_store_line_ids:
                if ln_where_store.mark_line_where_store == True:
                    ln_where_store.order_line_purchase_id.write({'where_to_store': self.where_to_store})


class WzPoDatePlannedLine(models.TransientModel):
    _name = 'wz.purchase.order.where.store.line'

    wz_po_where_store_id = fields.Many2one('wz.purchase.order.where.store', string='WZ po where store')
    mark_line_where_store = fields.Boolean('-', default=False)
    order_line_purchase_id = fields.Many2one('purchase.order.line', string='Order Line')
    product_id = fields.Many2one('product.product', string='Product', related='order_line_purchase_id.product_id', store=True)
    where_to_store = fields.Selection([
        ('inside', 'DENTRO'),
        ('doesnot_matter', 'DA IGUAL'),
        ('doesnot_apply', 'NO APLICA'),
    ], string="Dónde almacenar", related='order_line_purchase_id.where_to_store', store=True)
