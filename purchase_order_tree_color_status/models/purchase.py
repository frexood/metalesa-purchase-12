# -*- coding: utf-8 -*-

from odoo import models, fields


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _set_maximum_planned_date(self):
        for order in self:
            dates = order.order_line.mapped('date_planned')
            if dates:
                dates = max(dates)
            else:
                dates = False

            order.maximum_planned_date = dates

    maximum_planned_date = fields.Datetime(
        string="Maxima Fecha Planificada",
        compute=_set_maximum_planned_date,
    )
