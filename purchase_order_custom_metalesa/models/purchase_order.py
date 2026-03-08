# -*- coding: utf-8 -*-
# (c) 2020 Praxya - Miquel March <mmarch@praxya.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, exceptions, _
from odoo.exceptions import ValidationError, AccessError

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
        string=_('Fecha planificada'), 
    )

    where_to_store = fields.Selection([
        ('inside', 'DENTRO'),
        ('doesnot_matter', 'DA IGUAL'),
        ('doesnot_apply', 'NO APLICA'),
    ], string="Dónde almacenar", requered=True)

    @api.multi
    def _add_supplier_to_product(self):
        """Override para actualizar precios de supplierinfo existentes
        antes de llamar al super() que solo crea nuevos registros."""
        for line in self.order_line:
            # Determinar el partner (parent si es contacto)
            partner = self.partner_id if not self.partner_id.parent_id else self.partner_id.parent_id
            # Buscar supplierinfo existente para este partner y producto
            supplierinfo = self.env['product.supplierinfo'].search([
                ('name', '=', partner.id),
                ('product_tmpl_id', '=', line.product_id.product_tmpl_id.id),
                ('min_qty', '=', 0.0),
            ], limit=1, order='id desc')
            if supplierinfo:
                # Convertir el precio a la moneda del proveedor
                currency = partner.property_purchase_currency_id or self.env.user.company_id.currency_id
                price = self.currency_id._convert(
                    line.price_unit, currency, line.company_id,
                    line.date_order or fields.Date.today(), round=False)
                # Convertir el precio a la UdM de compra del producto si es diferente
                if line.product_id.product_tmpl_id.uom_po_id != line.product_uom:
                    default_uom = line.product_id.product_tmpl_id.uom_po_id
                    price = line.product_uom._compute_price(price, default_uom)
                try:
                    supplierinfo.write({
                        'price': price,
                        'currency_id': currency.id,
                    })
                except AccessError:
                    break
        return super(PurchaseOrder, self)._add_supplier_to_product()

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

    def add_DA_some_line(self):
        ctx = {}
        vals_po = {'purchase_order_id': self.id,}
        po_where_store = self.env['wz.purchase.order.where.store'].create(vals_po)

        po_ln_data = []
        for order_ln in self.order_line:
            po_ln_data.append((0, 0, {
                'product_id': order_ln.product_id.id,
                'order_line_purchase_id': order_ln.id,
                'where_to_store': self.where_to_store,
                'wz_po_where_store_id': po_where_store.id
            }))

        vals = {
            'purchase_order_id': self.id,
            'where_to_store': self.where_to_store,
            'po_where_store_line_ids': po_ln_data,
        }
        po_where_store.write(vals)

        get_lines = self.env['wz.purchase.order.where.store.line'].search([('wz_po_where_store_id','=',po_where_store.id)])

        ctx['default_id'] = po_where_store.id
        ctx['default_purchase_order_id'] = self.id
        ctx['default_where_to_store'] = self.where_to_store
        ctx['default_po_where_store_line_ids'] = get_lines.ids
        
        view_form_id = self.env.ref('purchase_order_custom_metalesa.view_wz_purchase_order_where_store_form').id

        return {
            'name': _('Asignar dónde almacenar'),
            'res_model': 'wz.purchase.order.where.store',
            'view_mode': 'form',
            'views': [[view_form_id, 'form']],
            'context': ctx,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def add_DA_allthe_lines(self):
        for orden_ln in self.order_line:
            orden_ln.write({'where_to_store': self.where_to_store})

    @api.multi
    def button_confirm(self):
        user = self.env.uid
        employee = self.env['hr.employee'].search([('user_id', '=', user)])
        if not self.where_to_store:
            raise ValidationError(_('Falta por rellenar el campo "Dónde almacenar"'))
        for line in self.order_line:
            if not line.where_to_store:
                raise ValidationError(_('Falta por rellenar el campo "Dónde almacenar" en la línea: %s') % 
                    (line.name or line.product_id.display_name))
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
    