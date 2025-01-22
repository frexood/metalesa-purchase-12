# -*- coding: utf-8 -*-

from odoo import models, api, _
from odoo.exceptions import ValidationError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_confirm(self):
        for order in self:
            if order.partner_id.blocked_supplier:
                raise ValidationError(_("PROVEEDOR BLOQUEADO. PREGUNTA A CONTABILIDAD O CALIDAD"))
        return super(PurchaseOrder, self).button_confirm()
    
    def validate_purchase(self):
        for order in self:
            if order.partner_id.blocked_supplier:
                raise ValidationError(_("PROVEEDOR BLOQUEADO. PREGUNTA A CONTABILIDAD O CALIDAD"))
        return super(PurchaseOrder, self).validate_purchase()
    
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """ Validación al seleccionar un proveedor en el Pedido de Compra """
        if self.partner_id and self.partner_id.blocked_supplier:
            self.partner_id = False
            raise ValidationError(_("PROVEEDOR BLOQUEADO. PREGUNTA A CONTABILIDAD O CALIDAD"))
        

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id.blocked_supplier:
            self.partner_id = False
            return {
                'warning': {
                    'title': _("Proveedor bloqueado"),
                    'message': _("PROVEEDOR BLOQUEADO. PREGUNTA A CONTABILIDAD O CALIDAD"),
                }
            }
        
class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id.blocked_supplier:
            self.partner_id = False
            return {
                'warning': {
                    'title': _("Proveedor bloqueado"),
                    'message': _("PROVEEDOR BLOQUEADO. PREGUNTA A CONTABILIDAD O CALIDAD"),
                }
            }
    