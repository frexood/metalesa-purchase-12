# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def get_cap_des(self):
        view_id_tree = self.env.ref('purchase_order_line_calendar.stock_move_tree_capacidad_carga_descarga_tree_view')

        return {
            'type': 'ir.actions.act_window',
            'name': _('Capacidad Carga/Descarga'),
            'res_model': 'stock.move',
            'view_type': 'form',
            'view_mode': 'tree,calendar',
            'view_id': view_id_tree.id,
            'views': [(view_id_tree.id, 'tree'), (False, 'form')],
            'target': 'current',
            'domain': [
                ('picking_type_id', '=', self.env.ref('stock.picking_type_in').id),
                ('mrp_galvanizado_id', '=', False),
                ('purchase_line_id', '!=', False)
            ]
        }

    date_planned_purchase_line_calendar = fields.Datetime(
        related='purchase_line_id.date_planned',
        string=_("Fecha Planificada")
    )

    purchase_id_calendar = fields.Many2one(
        related='purchase_line_id.order_id',
        string=_("Pedido")
    )

    fecha_ini_des = fields.Datetime(
        string=_("Fecha Ini Des"),
        related='purchase_line_id.fecha_ini_des',
        store=True,
    )

    fecha_fin_des = fields.Datetime(
        string=_("Fecha Fin Des"),
        related='purchase_line_id.fecha_fin_des',
        store=True,
    )

    picking_date_done = fields.Datetime(
        string=_("Fecha Transferencia"),
        related='picking_id.date_done',
    )

    es_recepcion = fields.Boolean(help='campo para poder poner en domain del action las recepciones', 
    compute='compute_es_recepcion')

    @api.depends('picking_code')
    def compute_es_recepcion(self):
        if self.picking_type_id == self.env.ref('stock.picking_type_in'):
            self.es_recepcion = True

