# -*- coding: utf-8 -*-

from odoo import fields, models, api, exceptions, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    email_calidad = fields.Boolean(
        string=_("Certificado de calidad")
    )

    @api.constrains('email_calidad')
    def _check_email_calidad(self):
        if self.parent_id:
            parent = self.parent_id
        else:
            parent = self

        checks = parent.child_ids.filtered(
            lambda x: x.email_calidad
        )

        if len(checks) > 1:
            raise exceptions.ValidationError(
                _('Existe más de un contacto con certificado de calidad\n' + '\n'.join(
                    checks.mapped('name')
                ))
            )

        if parent.email_calidad and len(checks) == 1:
            raise exceptions.ValidationError(
                _('La empresa padre %s y un contacto %s tienen el certificado de calidad ' % (
                    parent.name, ' '.join(checks.mapped('name'))
                ))
            )
