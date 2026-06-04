# -*- coding: utf-8 -*-

from odoo import fields, models, api


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    where_to_store = fields.Selection([
        ('inside', 'DENTRO'),
        ('doesnot_matter', 'DA IGUAL'),
        ('doesnot_apply', 'NO APLICA'),
    ], string="Dónde almacenar", required=False)

    @api.model
    def create(self, vals):
        """
        Al CREAR una línea nueva cuyo producto sea cualquier variante de
        SERVICIO DE TRANSPORTE, rellena automáticamente 'Dónde almacenar'
        con 'NO APLICA' (requisito confirmado por César Valero, 15/12).

        Solo se aplica si el valor no viene ya informado, para no pisar una
        elección explícita del usuario.
        """
        if not vals.get('where_to_store') and vals.get('product_id'):
            product = self.env['product.product'].browse(vals['product_id'])
            if product and product.name and 'TRANSPORTE' in product.name.upper():
                vals['where_to_store'] = 'doesnot_apply'
        return super(PurchaseOrderLine, self).create(vals)

    # NOTA (EVO663): El onchange '_onchange_product_id_check_transport' se
    # eliminó por petición de César Valero (15/12). Era redundante porque al
    # duplicar el campo 'Dónde almacenar' ya se copia, y el usuario siempre lo
    # informa manualmente. El relleno automático de 'NO APLICA' para transporte
    # ahora se hace SOLO al crear la línea (método create de arriba).