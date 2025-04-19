# -*- coding: utf-8 -*-
# (c) 2020 Praxya - Miquel March <mmarch@praxya.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, _

class StockMove(models.Model):
    _inherit = 'stock.move'

    where_to_store = fields.Selection([
        ('inside', 'DENTRO'),
        ('doesnot_matter', 'DA IGUAL'),
        ('doesnot_apply', 'NO APLICA'),
    ], string="Dónde almacenar", related='purchase_line_id.where_to_store', store=True)

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    where_to_store = fields.Selection([
        ('inside', 'DENTRO'),
        ('doesnot_matter', 'DA IGUAL'),
        ('doesnot_apply', 'NO APLICA'),
    ], string="Dónde almacenar", related='move_id.where_to_store', store=True)


    def get_where_to_store_display(self):
        self.ensure_one()
        selection = dict(self._fields['where_to_store'].selection(self))
        return _(selection.get(self.where_to_store))
