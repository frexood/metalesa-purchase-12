# -*- coding: utf-8 -*-
# (c) 2020 Praxya - Miquel March <mmarch@praxya.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, exceptions, _
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string=_("Employee"),
        invisible=True
    )

    @api.multi
    def button_confirm(self):
        user = self.env.uid
        employee = self.env['hr.employee'].search([('user_id', '=', user)])
        if not bool(employee):
            user_name = self.env['res.users'].browse(user).name
            error_msg = "No existe un empleado válido para el usuario '{}'.\n".format(user_name)
            error_msg += "No se puede asignar un 'Responsable de compra'❗"
            raise ValidationError(error_msg)
        res = super(PurchaseOrder, self).button_confirm()
        return res

    @api.multi
    def button_approve(self):
        res = super(PurchaseOrder, self).button_approve()
        required_fields = []
        if not self.user_id:
            required_fields.append("Responsable de compra")
        if not self.payment_mode_id:
            required_fields.append('Modo de pago')
        if not self.payment_term_id:
            required_fields.append('Plazos de pago')
        # if not self.supplier_partner_bank_id:
        #     required_fields.append('Cuenta bancaria del proveedor')
        if not self.fiscal_position_id:
            required_fields.append('Posición fiscal')
        if len(required_fields) > 0:
            mensaje_error = 'Para confirmar el presupuesto de compra faltan por rellenar: '
            for field in required_fields:
                mensaje_error += ('[' + field + '] ')
            raise exceptions.ValidationError(mensaje_error)
        return res

    @api.model
    def default_get(self, fields):
        res = super(PurchaseOrder, self).default_get(fields)

        # empleado = self.env['hr.employee'].search([('user_id','=', self._context.get('uid'))])
        # if (empleado):
        res['user_id'] = self._context.get('uid')
        return res

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        if default is None:
            default = {}
        default['user_id'] = self.env.user.id
        return super(PurchaseOrder, self).copy(default)