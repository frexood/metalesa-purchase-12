# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import base64


class PurchaseOrderResponsability(models.TransientModel):
    _name = 'purchase.order.responsability'
    _description = _('Check de responsabilidad/comparativo')
    
    comparativa_ok = "Confirmo que he realizado el comparativo, que está adjunto en este PC, y que está en carpeta de proyecto en servidor"
    comparativa_rechazar = "Lanzo la compra sin haber hecho el comparativo y a continuación explico el/los motivo/s."
    
    ## FIELDS ###
    
    pedido_compra_id = fields.Many2one('purchase.order')
    responsabilidad_selection = fields.Selection([('aceptar', comparativa_ok),('rechazar', comparativa_rechazar)], string=_('Check responsabilidad'))
    explicacion_ausencia = fields.Text(string=_('Explicación ausencia'))

    ### FUNCTIONS ###
    
    def confirmar(self):
        if self.responsabilidad_selection == 'rechazar':
            self.pedido_compra_id.message_post(body=self.explicacion_ausencia)
        self.pedido_compra_id.button_confirm()
        
        