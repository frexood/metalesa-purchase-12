# -*- coding: utf-8 -*-
# (c) 2020 Praxya - Miquel March <mmarch@praxya.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, exceptions, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def abrir_wizard_responsabilidad(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Check de responsabilidad/comparativo',
            'view_mode': 'form',
            'view_id': self.env.ref('purchase_order_responsability_check.purchase_order_responsability_view_form').id,
            'target': 'new',
            'res_model': 'purchase.order.responsability',
            'context': {
                'default_pedido_compra_id': self.id,
                'default_responsabilidad_selection': 'aceptar',
            } 
        }