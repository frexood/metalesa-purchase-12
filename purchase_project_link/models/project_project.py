# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProjectProjectExtends(models.Model):
    _inherit = 'project.project'

    @api.multi
    def compute_purchase_count(self):
        for i in self:
            i.purchase_count = len(self.env['purchase.order.line'].search([
                ('account_analytic_id', 'in', i.cuentas_analiticas_ids.ids)
            ]))

    purchase_count = fields.Integer(
        string=_('Project Count'),
        compute=compute_purchase_count
    )

    @api.multi
    def get_purchases(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Purchase Orders'),
            'view_type': 'form',
            'view_mode': 'form,tree',
            'view_id': self.env.ref('purchase_order_line_view.purchase_line_form_view_metalesa_custom_tree').id,
            'views': [
                (self.env.ref('purchase_order_line_view.purchase_line_form_view_metalesa_custom_tree').id, 'tree'),
                (self.env.ref('purchase.purchase_order_line_form2').id, 'form')
            ],
            'res_model': 'purchase.order.line',
            'domain': [('id', 'in', self.env['purchase.order.line'].search([
                ('account_analytic_id', '=', self.cuentas_analiticas_ids.ids)
            ]).ids)],
            'target': 'current',
        }
