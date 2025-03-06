# -*- coding: utf-8 -*-
# (c) 2020 Praxya - Miquel March <mmarch@praxya.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, exceptions, _
from odoo.exceptions import ValidationError

from pytz import timezone

import pytz

import logging
_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string=_("Employee"),
        invisible=True
    )

    date_planned_pc_lines = fields.Datetime(
        string=_('Fecha planificada en todas las líneas'), 
    )


    def add_date_planned(self):
        ctx = {}
        # generate id
        vals_create = {
                    'purchase_order_id': self.id,
        }
        res_create = self.env['wz.purchase.order.date.planned'].create(vals_create)
        list_data = []
        for rec_p in self.order_line:
            list_data.append((0,0,{
                    'product_id': rec_p.product_id.id,
                    'order_line_purchase_id': rec_p.id,
                    'date_planned_pc_line': self.date_planned,
                    'wz_po_date_planned_id': res_create.id
                    }))
            
        vals_write = {
                    'date_planned_pc_line': self.date_planned_pc_lines,
                    'purchase_order_id': self.id,
                    'order_line_po_ids': list_data,
        }
        res_write = res_create.write(vals_write)

        get_lines = self.env['wz.po.date.planned.line'].search([('wz_po_date_planned_id','=',res_create.id)])

        ctx['default_id'] = res_create.id
        ctx['default_purchase_order_id'] = self.id
        ctx['default_date_planned_pc_line'] = self.date_planned_pc_lines
        ctx['default_order_line_po_ids'] = get_lines.ids
        
        view_form_id = self.env.ref('purchase_order_custom_metalesa.view_wz_purchase_order_date_planned_form').id

        return {
            'name': _('Asignar fecha planificada'),
            'res_model': 'wz.purchase.order.date.planned',
            'view_mode': 'form',
            'views': [[view_form_id, 'form']],
            'context': ctx,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def add_date_all_planned(self):
        user_tz = self.env.user.tz or 'UTC'  # Obtener la zona horaria del usuario
        tz = pytz.timezone(user_tz)

        for rec in self.order_line:
            date_planned = fields.Datetime.to_datetime(self.date_planned_pc_lines)
            date_planned = date_planned.replace(hour=9, minute=0, second=0)
            date_utc = tz.localize(date_planned).astimezone(pytz.utc).replace(tzinfo=None)
            rec.write({'date_planned': date_utc})
            #self.date_planned_pc_lines = ''



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