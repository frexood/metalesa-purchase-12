# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _

from datetime import datetime, timedelta
import pytz



class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.depends('date_planned', 'planned_hour', 'load_time')
    def _compute_load_dates(self):
        for record in self:
            if record.date_planned:
                my_tz = pytz.timezone(self._context.get('tz') or 'UTC')

                date_planned1 = fields.Datetime.from_string(record.date_planned)

                offset = my_tz.utcoffset(date_planned1).total_seconds() / 3600.0

                date_ini = date_planned1 + timedelta(hours=record.planned_hour - offset)
                date_end = date_planned1 + timedelta(hours=record.planned_hour - offset, minutes=int(record.load_time))

                record.fecha_ini_des = date_ini
                record.fecha_fin_des = date_end

    @api.multi
    def write(self, vals):
        if 'fecha_ini_des' in vals:
            d = fields.Datetime.from_string(vals['fecha_ini_des'])

            my_tz = pytz.timezone(self._context.get('tz') or 'UTC')

            offset = my_tz.utcoffset(d).total_seconds() / 3600.0
            h = offset + d.hour + (d.minute / 60.0) + (d.second / 3600.0)

            vals['planned_hour'] = h

        return super(PurchaseOrderLine, self).write(vals)

    planned_hour = fields.Float(
        string=_("Hora Planificada"),
        default=0.0,
    )

    load_time = fields.Selection(
        selection=[
            ('15', _('15 minutos')),
            ('60', _('1 Hora')),
            ('120', _('2 Horas')),
        ],
        string=_("Tiempo Carga/Descarga"),
        required=True,
        default='15',
    )

    fecha_ini_des = fields.Datetime(
        string=_("Fecha Ini Des"),
        compute=_compute_load_dates,
        store=True,
    )

    fecha_fin_des = fields.Datetime(
        string=_("Fecha Fin Des"),
        compute=_compute_load_dates,
        store=True,
    )

    @api.onchange('fecha_ini_des', 'fecha_fin_des')
    def onchange_recompute_purchase_line(self):
        for record in self:
            moves = record.move_ids.filtered(
                lambda x: self.state not in ('done', 'draft', 'cancel')
            )

            if moves:
                moves.write({
                    'fecha_ini_des': record.fecha_ini_des,
                    'fecha_fin_des': record.fecha_fin_des,
                })
