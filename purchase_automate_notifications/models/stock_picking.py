# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)



class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def action_done(self):
        res = super(StockPicking, self).action_done()

        # Cacheando solo una vez
        config = self.env['purchase.notification.config'].sudo().search([], limit=1)
        if not config or not config.type_picking_ids:
            return res  # Nada que hacer

        # Obtener IDs permitidos en una sola vez
        allowed_picking_type_ids = set(config.type_picking_ids.ids)

        # Filtrar en bucle nativo, más rápido que ORM filtered()
        create_vals = []
        for picking in self:
            if (
                picking.picking_type_id.code == 'incoming' and
                picking.picking_type_id.id in allowed_picking_type_ids
            ):
                create_vals.append({'picking_id': picking.id})

        # Crear en batch si hay varios
        if create_vals:
            self.env['purchase.receive.notification'].sudo().create(create_vals)
            _logger.info("Notificaciones creadas para pickings: %s", [v['picking_id'] for v in create_vals])

        return res

    """@api.multi
    def action_done(self):
        res = super(StockPicking, self).action_done()
        for picking in self.filtered(lambda p: p.picking_type_id.code == 'incoming'):
            self.env['purchase.receive.notification'].create({'picking_id': picking.id})

        return res"""
    


