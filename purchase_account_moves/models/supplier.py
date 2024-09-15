# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _compute_account_moves(self):
        for record in self:
            record.purchase_count_account_moves = len(
                self.env['account.move.line'].search([('partner_id', '=', record.id)
                                                      ])
            )

    purchase_count_account_moves = fields.Integer(
        compute=_compute_account_moves
    )

    @api.multi
    def open_account_moves(self):
        view = self.env.ref('account.view_move_line_tree')
        purchases = self.env['account.move.line'].search([
            ('partner_id', '=', self.id)])

        return {
            'name': _('Apuntes Contables'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(view.id, 'tree')],
            'res_model': 'account.move.line',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [('id', 'in', purchases.ids)]
        }
