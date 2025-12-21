# -*- coding: utf-8 -*-

from odoo import fields, models, api


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    where_to_store = fields.Selection([
        ('inside', 'DENTRO'),
        ('doesnot_matter', 'DA IGUAL'),
        ('doesnot_apply', 'NO APLICA'),
    ], string="Dónde almacenar", required=False)


    @api.onchange('product_id')
    def _onchange_product_id_check_transport(self):
        """
        Detecta cambios en el campo product_id.
        Si el nombre del producto contiene 'TRANSPORTE', asigna 'doesnot_apply'.
        """
        if self.product_id and self.product_id.name:
            # Usamos .upper() para que funcione con 'Transporte', 'transporte' o 'TRANSPORTE'
            if 'TRANSPORTE' in self.product_id.name.upper():
                self.where_to_store = 'doesnot_apply'
            else:
                # Opcional: Si quieres reiniciar el valor si cambian a un producto que NO es transporte
                # Si no quieres que se reinicie, borra las siguientes lineas:
                if self.where_to_store == 'doesnot_apply':
                     self.where_to_store = False