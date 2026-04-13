# -*- coding: utf-8 -*-
# (c) 2020 Praxya - Miquel March <mmarch@praxya.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class ProductPurchaseHistory(models.Model):
    """
    Modelo transaccional que almacena el historial de compras de variantes de producto.
    Obtiene datos de órdenes de compra realizadas (done/purchase) para un producto específico.
    """
    _name = 'product.purchase.history'
    _description = 'Historial de compras de producto'
    _order = 'partner_name asc, date_order desc'
    _auto = False
    _rec_name = 'id'

    # Campos que representan la consulta SQL
    product_id = fields.Many2one('product.product', string='Producto', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Proveedor', readonly=True)
    partner_name = fields.Char(string='Nombre del Proveedor', readonly=True)
    purchase_order_id = fields.Many2one('purchase.order', string='Orden de Compra', readonly=True)
    purchase_order_name = fields.Char(string='Número de OC', readonly=True)
    date_order = fields.Date(string='Fecha de Pedido', readonly=True)
    price_unit = fields.Float(string='Precio Unitario', readonly=True, digits=(12, 4))
    product_uom = fields.Many2one('uom.uom', string='Unidad de Medida', readonly=True)
    product_qty = fields.Float(string='Cantidad', readonly=True, digits=(16, 2))
    currency_id = fields.Many2one('res.currency', string='Moneda', readonly=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('purchase', 'Confirmada'),
        ('done', 'Procesada'),
        ('cancel', 'Cancelada'),
    ], string='Estado', readonly=True)
    purchase_order_line_id = fields.Many2one('purchase.order.line', string='Línea de OC', readonly=True)

    def init(self):
        """
        Crear la vista SQL que alimenta este modelo transaccional.
        Ejecuta la consulta SQL para obtener el historial de compras.
        """
        # Eliminar la vista anterior si existe
        self.env.cr.execute("""
            DROP VIEW IF EXISTS product_purchase_history CASCADE;
        """)
        
        # Crear la nueva vista SQL con la consulta del usuario
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW product_purchase_history AS
            SELECT 
                pol.id,
                pol.product_id,
                rp.id as partner_id,
                rp.name as partner_name,
                po.id as purchase_order_id,
                po.name as purchase_order_name,
                po.date_order::date as date_order,
                pol.price_unit,
                pol.product_uom,
                pol.product_qty,
                po.currency_id,
                pol.state,
                pol.id as purchase_order_line_id
            FROM purchase_order_line pol
            INNER JOIN purchase_order po ON po.id = pol.order_id
            INNER JOIN res_partner rp ON rp.id = po.partner_id
            INNER JOIN product_product pp ON pp.id = pol.product_id
            WHERE pol.state IN ('done', 'purchase');
        """)

    @api.model
    def debug_view_data(self):
        """
        Método para debuguear y ver qué datos contiene la vista SQL.
        Retorna información útil para diagnosticar problemas.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Ejecutar SQL directo para ver si la vista existe y qué datos tiene
        try:
            self.env.cr.execute("""
                SELECT COUNT(*) FROM product_purchase_history;
            """)
            count = self.env.cr.fetchone()[0]
            logger.info(f"[DEBUG] Total de registros en product_purchase_history: {count}")
            
            # Mostrar primeros 5 registros
            self.env.cr.execute("""
                SELECT product_id, partner_name, purchase_order_name, date_order, price_unit 
                FROM product_purchase_history 
                LIMIT 5;
            """)
            rows = self.env.cr.fetchall()
            for row in rows:
                logger.info(f"[DEBUG] Registro: product_id={row[0]}, partner={row[1]}, order={row[2]}, date={row[3]}, price={row[4]}")
            
            return {
                'total_records': count,
                'sample_records': rows
            }
        except Exception as e:
            logger.error(f"[DEBUG] Error accediendo a vista: {str(e)}")
            return {'error': str(e)}

