# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class WzPurchaseOrderDatePlanned(models.TransientModel):
    _name = 'wz.purchase.order.date.planned'
    _description = _('WzPurchaseOrderDatePlanned')

    name = fields.Char(_('Name'))

    purchase_order_id = fields.Many2one('purchase.order', string='purchase_order')
    state = fields.Selection( string='Estate', related='purchase_order_id.state',store=True)

    order_line_po_ids = fields.One2many('wz.po.date.planned.line', 'wz_po_date_planned_id', string='Order Line')

    date_planned_pc_line = fields.Datetime(string=_('Asignar Fecha planificada'))

    def assign_date_planned_line(self):
        res_po = self.env['purchase.order'].search([('id','=',self.purchase_order_id.id)])
        if res_po:
            for rec in self.order_line_po_ids:
                if rec.check_line_porder_id == True:
                    rec.order_line_purchase_id.write({'date_planned': self.date_planned_pc_line})



class WzPoDatePlannedLine(models.TransientModel):
    _name = 'wz.po.date.planned.line'

    date_planned_pc_line = fields.Datetime(string=_('Fecha planificada'))

    check_line_porder_id = fields.Boolean('-',default=False)
    order_line_purchase_id = fields.Many2one('purchase.order.line', string='Order Line')
    product_id = fields.Many2one('product.product', string='product')
    
    wz_po_date_planned_id = fields.Many2one('wz.purchase.order.date.planned', string='WZ po assign')