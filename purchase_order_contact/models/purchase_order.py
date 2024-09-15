# -*- encoding: utf-8 -*-

from odoo import models, fields, _


class PurchaseOrderContact(models.Model):
    _inherit = 'purchase.order'

    contact_id = fields.Many2one(
        string=_('A/A'),
        comodel_name='res.partner',
        help=_('Indicates the contact of partner')
    )
    