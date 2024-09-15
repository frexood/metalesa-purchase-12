# -*- coding: utf-8 -*-

from odoo import fields, models, api, exceptions, _


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    email_cert_calidad = fields.Char(
        string=_('Email certificado calidad'),
        related="order_id.email_cert_calidad",
        store=True,
    )


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    email_cert_calidad = fields.Char(
        string=_("Email Certificado Calidad")
    )

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        res = super(PurchaseOrder, self).onchange_partner_id()

        if self.partner_id:
            res = {'value': {}}

            partner_ids = self.partner_id.child_ids.filtered(
                lambda x: x.email_calidad and x.email
            )

            if partner_ids:
                mail_cert = {'email_cert_calidad': ','.join(partner_ids.mapped('email'))}
            else:
                mail_cert = {'email_cert_calidad': self.partner_id.email}

            res['value'].update(mail_cert)

        return res
