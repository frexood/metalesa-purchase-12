# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class WzPurchaseOrderDuplicateLine(models.TransientModel):
    _name = 'wz.purchase.order.duplicate.line'
    _description = _('WzPurchaseOrderDuplicateLine')

    
    purchase_order_id = fields.Many2one('purchase.order', string='Actual')
    purchase_order_dest_id = fields.Many2one('purchase.order', string='Destino')

    line_ids = fields.One2many(
        'wz.po.duplicate.lines', 'wz_po_duplicate_line_id', string="Líneas de pedido"
    )

    @api.model
    def default_get(self, fields):
        records = super(WzPurchaseOrderDuplicateLine, self).default_get(fields)
        sale_ids = self._context.get('active_ids')
        if len(sale_ids)>=1:
            sale_id = self.env['purchase.order'].browse(sale_ids[0])
            lineas = []
            for line in sale_id.order_line:
                vals = (0,0, {
                    'purchase_orde_line_id': line.id,
                    'product_id': line.product_id.id,
                    'description': line.name,
                })
                lineas.append(vals)

            records['purchase_order_id'] = sale_id.id
            records['line_ids'] = lineas

        return records

    def copy_lines(self):
        if bool(self.purchase_order_dest_id.id):
            for line in self.line_ids:
                if line.selected:
                    for _ in range(line.selected) :
                        line.purchase_orde_line_id.copy({
                            'order_id': self.purchase_order_dest_id.id
                        })



class WzPoDuplicateLines(models.TransientModel):
    _name = 'wz.po.duplicate.lines'
    _description = _('WzPurchaseOrderDuplicateLine')

    purchase_orde_line_id = fields.Many2one(
        comodel_name='purchase.order.line',
        string='Líneas de pedido',
    )

    selected = fields.Integer(
        string="Nº Duplicados", default=0,
    )

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Producto',
    )

    description = fields.Text(
        translate=True,
        string='Descripción',
    )

    wz_po_duplicate_line_id = fields.Many2one('comodel_name', string='Lines')