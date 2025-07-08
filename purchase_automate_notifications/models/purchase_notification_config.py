# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)



class PurchaseNotificationConfig(models.Model):
    _name = 'purchase.notification.config'
    _description = 'Configuración de notificaciones de recepción de compras'

    user_ids = fields.Many2many('res.users', string="Usuarios a Notificar")
    employee_ids = fields.Many2many('hr.employee', string="Usuarios a notificar")

