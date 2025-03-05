# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
import logging
import re 

_logger = logging.getLogger(__name__)  


class PurchaseOrderExtends(models.Model):
    _inherit = 'purchase.order'


    def addTermsAndConditions(self):
        return self.env['terms.and.conditions.wizard'].getWizard(
            self.id,
            self._name,
            'notes',
            False
        )


    def write(self, vals):
        """
        Al guardar, si 'notes' está vacío (o solo contiene HTML vacío) y hay productos
        sin términos en la orden, se llenará con los términos por defecto.
        """
        notes_content = vals.get('notes', self.notes)
        cleaned_notes = self._clean_html(notes_content)

        has_products_without_terms = self._has_products_without_terms(vals)

        _logger.info("Estado de notes después de limpieza: %s", cleaned_notes)
        if has_products_without_terms:
            _logger.info("Se detectaron productos sin términos: Sí")

        if not cleaned_notes.strip() and has_products_without_terms:
            _logger.info("El campo 'notes' está vacío y hay productos sin términos, asignando valor por defecto...")
            vals['notes'] = self._get_default_terms()
        else:
            _logger.info("No se modifica 'notes' porque ya tiene contenido o no hay productos sin términos.")

        return super(PurchaseOrderExtends, self).write(vals)

    def copy(self, default=None):
        """
        Evita que 'notes' se llene al duplicar la orden.
        """
        default = dict(default or {})
        default['notes'] = False 

        _logger.info("======= DEBUG: copy() ejecutado =======")
        _logger.info("Valores en default: %s", default)

        return super(PurchaseOrderExtends, self).copy(default)

    def _get_default_terms(self):
        """
        Obtiene los términos y condiciones predeterminados y los devuelve.
        """
        _logger.info("Buscando términos y condiciones predeterminados...")

        terms = self.env['terms.and.conditions'].search([
            ('default', '=', True),("type","=","purchase")
        ])
        
        if terms:
            _logger.info("Se encontraron términos y condiciones, asignando...")
            comment = '<ul>'
            for term in terms:
                comment += '<li>{}</li>'.format(term.description)
            comment += '</ul>'
            return comment
        else:
            _logger.info("No se encontraron términos y condiciones predeterminados.")
            return ''

    def _has_products_without_terms(self, vals=None):
        """
        Verifica si alguno de los productos en la orden de compra NO está en `products.terms.and.conditions`.
        Retorna `True` si hay productos sin términos, `False` si todos los productos tienen términos.
        """
        _logger.info("Verificando si los productos de la orden tienen términos asignados...")

        product_ids = set(self.order_line.mapped('product_id.id')) 

        if vals and 'order_line' in vals:
            for line in vals['order_line']:
                if line[0] in (0, 4):  
                    product_id = line[2].get('product_id') if isinstance(line[2], dict) else line[1]
                    if product_id:
                        product_ids.add(product_id)

        if not product_ids:
            return False  

        products_with_terms = self.env['products.terms.and.conditions'].search([
            ('product_product_id', 'in', list(product_ids))
        ]).mapped('product_product_id.id')

        products_without_terms = product_ids - set(products_with_terms)

        _logger.info("Productos sin términos: %s", products_without_terms)

        return bool(products_without_terms)  

    def _clean_html(self, text):
        """
        Limpia etiquetas HTML vacías y devuelve un string vacío si no hay contenido real.
        """
        if not text:
            return ''
        
        clean_text = re.sub(r'<(p|br|div|span|strong|em|u|i|b)>\s*</\1>', '', text)
        clean_text = re.sub(r'<[^>]+>', '', clean_text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()

        return clean_text
