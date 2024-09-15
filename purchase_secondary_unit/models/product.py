# -*- encoding: utf-8 -*-

from odoo import models, fields, _
from odoo.addons import decimal_precision as dp


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    uop_id = fields.Many2one(
        comodel_name='uom.uom',
        string=_('Secondary Unit of Purchase'),
        help=_("""Specify a unit of measure here if purchasing is made in another
            unit of measure category than inventory. Keep empty to use the
            default unit of measure.""")
    )

    uop_coeff = fields.Float(
        string=_('Purchase Unit of Measure -> 2UoP Coeff'),
        digits=dp.get_precision('Product UoP'),
        help=_("""Coefficient to convert default Purchase Unit of Measure to
            Secondary Unit of Purchase\n uop = uom * coeff"""),
        default=1.0
    )


# migrado de la v8 product_uop_coeff_per_variant
class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    uop_coeff = fields.Float(
        string='Purchase Unit of Measure -> 2UoP Coeff',
        digits=dp.get_precision('Product UoP'),
        help='Coefficient to convert default Purchase Unit of Measure to'
        ' Secondary Unit of Purchase\n uop = uom * coeff', 
        default=1.0,
    )