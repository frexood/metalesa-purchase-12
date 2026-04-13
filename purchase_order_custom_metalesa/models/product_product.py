# -*- coding: utf-8 -*-
# (c) 2020 Praxya - Miquel March <mmarch@praxya.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _


class ProductProductCustom(models.Model):
    """
    Extensión del modelo product.product para agregar historial de compras.
    El historial se obtiene dinámicamente desde el modelo product.purchase.history
    que se alimenta de una vista SQL transaccional.
    """
    _inherit = 'product.product'

    # Campo one2many que referencia el historial de compras dinámicamente
    # Este campo obtiene los registros del modelo transaccional product.purchase.history
    purchase_history_ids = fields.One2many(
        comodel_name='product.purchase.history',
        compute='_compute_purchase_history',
        string='Historial de Compras',
        help='Historial de últimas compras confirmadas o procesadas para esta variante de producto'
    )

    @api.depends()
    def _compute_purchase_history(self):
        """
        Calcula el historial de compras para cada variante de producto.
        Realiza una búsqueda en el modelo transaccional product.purchase.history
        filtrado por el product_id actual.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        for product in self:
            logger.info(f"[HISTORY] Buscando historial para product_id={product.id}")
            
            # Buscar TODOS los registros primero para verificar si hay datos
            all_records = self.env['product.purchase.history'].search([], limit=10)
            logger.info(f"[HISTORY] Total de registros en la vista: {len(all_records)}")
            
            if all_records:
                for rec in all_records[:3]:
                    logger.info(f"[HISTORY] Registro encontrado - product_id={rec.product_id.id}, partner={rec.partner_name}")
            
            # Ahora buscar específicamente para este producto
            history_records = self.env['product.purchase.history'].search([
                ('product_id', '=', product.id)
            ], order='date_order desc, partner_name asc')
            
            logger.info(f"[HISTORY] Encontrados {len(history_records)} registros para product_id={product.id}")
            
            # Asignar los registros encontrados al campo one2many
            product.purchase_history_ids = history_records

