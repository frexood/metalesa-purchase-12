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
        for picking in self.filtered(lambda p: p.picking_type_id.code == 'incoming'):
            print("----------------------->aqui va<-----------------------------")
            self.env['purchase.receive.notification'].create({'picking_id': picking.id})



        return res