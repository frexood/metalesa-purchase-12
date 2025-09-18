# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)



class PurchaseNotificationConfig(models.Model):
    _name = 'purchase.notification.config'
    _description = 'Configuración de notificaciones de recepción de compras'

    name = fields.Char(string=('Configuración de Notificaciones'),default="Configuración de Notificaciones")
    user_ids = fields.Many2many('res.users', string="Usuarios a Notificar")
    employee_ids = fields.Many2many(
        'hr.employee',
        'your_model_employee_notify_rel',  # Nombre único para la tabla de relación
        'your_model_id', 'employee_id',
        string="Usuarios a notificar"
    )

    employee_bad_inspection_ids = fields.Many2many(
        'hr.employee',
        'your_model_employee_bad_insp_rel',  # Otro nombre único
        'your_model_id', 'employee_id',
        string="Usuarios Novedad en inspecciones"
    )