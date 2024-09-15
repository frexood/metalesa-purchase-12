# -*- coding: utf-8 -*-

from odoo import fields, models, api


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    _order = 'create_date asc'

    certification_needed = fields.Boolean(
        string='¿Necesita Certificado?',
        readonly=False,
        states={
            'confirmed': [('readonly', False)],
            'done': [('readonly', False)]
        }
    )

    certification_received = fields.Boolean(
        string='¿Certificado recibido?',
        readonly=False,
        states={
            'confirmed': [('readonly', False)],
            'done': [('readonly', False)]
        }
    )

    @api.multi
    def certification_true(self):
        for line in self:
            if line.certification_needed:
                line.certification_needed = False
            elif not line.certification_needed:
                line.certification_needed = True

    @api.multi
    def certification_received_true(self):
        for line in self:
            if line.certification_received:
                line.certification_received = False
            elif not line.certification_received:
                line.certification_received = True
