# Copyright 2016 Jairo Llopis <jairo.llopis@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.addons import decimal_precision as dp

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    
    @api.onchange('invoice_line_ids')
    def onchange_lines(self):
        if self.type == 'in_invoice':
            for record in self.invoice_line_ids:
                record._onchange_facturar_a_mano()
    
class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    price_unit_uop = fields.Float(string='Unit Price UOP', required=True, digits=dp.get_precision('Product Price'))

    product_uop_qty = fields.Float(string='Quantity', digits=dp.get_precision('Product Unit of Measure'),
                            required=True, default=1)

    qty_received = fields.Float(string="Received Qty", digits=dp.get_precision('Product Unit of Measure'), copy=False)

    cantidad_recibida = fields.Float(string="Other Qty", digits=dp.get_precision('Product Unit of Measure'))

    product_uop_id = fields.Many2one('uom.uom', string='Unit of Measure',
        ondelete='set null', index=True, oldname='uos_id')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            purchase_order_line_id = vals.get('purchase_line_id')
            purchase_order_line = self.env['purchase.order.line'].browse(purchase_order_line_id)

            account_id = self.search([]).browse(purchase_order_line_id)
            if account_id:
                vals.update(
                    price_unit_uop=purchase_order_line.price_unit_uop,
                    product_uop_id=purchase_order_line.product_uop.id,
                    product_uop_qty=purchase_order_line.product_uop_qty,
                    qty_received=purchase_order_line.qty_received,
                    cantidad_recibida=purchase_order_line.product_uop_qty * purchase_order_line.qty_received / purchase_order_line.product_qty
                )
        return super(AccountInvoiceLine, self).create(vals_list)

    @api.depends('cantidad_recibida', 'price_unit_uop')
    @api.onchange('cantidad_recibida', 'price_unit_uop')
    def _onchange_facturar_a_mano(self):
        for record in self:
            vals = {'quantity': record.cantidad_recibida,
                    'price_unit': record.price_unit_uop,
                    'uom_id': record.product_uop_id.id,
                    }
            record.update(vals)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        res = super(AccountInvoiceLine, self)._onchange_product_id()

        self.product_uop_id = self.product_id.uom_po_id or self.product_id.uom_id
        if not self.cantidad_recibida:
            self.cantidad_recibida = 1
        price_unit_uop = self.product_id.uop_coeff * self.cantidad_recibida
        self.price_unit_uop = price_unit_uop
        self.price_unit = price_unit_uop
        return res
