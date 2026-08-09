# -*- coding: utf-8 -*-# -*- encoding: utf-8 -*-

from asyncio.log import logger

from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero, html_escape


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def action_repair_uop_before_invoice(self):
        """Repair missing/inconsistent secondary purchase values safely.

        This is intentionally a recovery action, not part of the regular
        invoicing flow.  Stock quantities and existing invoices are only read;
        the only records written are the affected purchase order lines.
        """
        if not self:
            raise UserError(_('Seleccione al menos un pedido de compra.'))
        if not self.env.user.has_group('purchase.group_purchase_manager'):
            raise UserError(_(
                'Solo un responsable de compras puede ejecutar esta acción.'
            ))

        self.check_access_rights('write')
        self.check_access_rule('write')

        blocked = []
        repair_plan = []
        reports = {}

        for order in self:
            if order.state not in ('purchase', 'done'):
                blocked.append(_(
                    '%s: el pedido debe estar confirmado o bloqueado.'
                ) % order.display_name)
                continue
            if not order.order_line:
                blocked.append(_('%s: el pedido no tiene líneas.') % order.display_name)
                continue

            reports[order.id] = {
                'repaired': [],
                'already_ok': 0,
                'not_pending': 0,
            }

            for line in order.order_line:
                product = line.product_id
                rounding = line.product_uom.rounding if line.product_uom else 0.01

                if not product or not line.product_uom:
                    blocked.append(_(
                        '%s, línea %s: falta el producto o la unidad de medida.'
                    ) % (order.display_name, line.id))
                    continue

                if product.purchase_method == 'purchase':
                    pending_qty = line.product_qty - line.qty_invoiced
                else:
                    pending_qty = line.qty_received - line.qty_invoiced

                if float_compare(pending_qty, 0.0, precision_rounding=rounding) < 0:
                    blocked.append(_(
                        '%s, línea %s (%s): la cantidad facturada supera la '
                        'cantidad facturable.'
                    ) % (order.display_name, line.id, product.display_name))
                    continue
                if float_is_zero(pending_qty, precision_rounding=rounding):
                    reports[order.id]['not_pending'] += 1
                    continue

                # account_invoice_secondary_values currently rebuilds the
                # secondary invoice quantity from cumulative qty_received.
                # It is safe for the first bill, but not after a partial bill.
                # Do not disguise that separate issue by changing PO data.
                if (
                    product.purchase_method == 'receive' and
                    float_compare(
                        line.qty_invoiced, 0.0,
                        precision_rounding=rounding,
                    ) > 0
                ):
                    blocked.append(_(
                        '%s, línea %s (%s): ya existe una facturación parcial '
                        'y queda cantidad recibida pendiente. Este caso debe '
                        'revisarse antes de generar otra factura.'
                    ) % (order.display_name, line.id, product.display_name))
                    continue

                # The same customization uses received quantity even for
                # products configured to bill ordered quantities.  Only the
                # fully received, never-before-billed case is safe here.
                if product.purchase_method == 'purchase' and (
                    not float_is_zero(
                        line.qty_invoiced, precision_rounding=rounding
                    ) or float_compare(
                        line.qty_received, line.product_qty,
                        precision_rounding=rounding,
                    ) != 0
                ):
                    blocked.append(_(
                        '%s, línea %s (%s): el producto se factura por '
                        'cantidad pedida, pero la personalización actual usa '
                        'la cantidad recibida. Se requiere revisión manual.'
                    ) % (order.display_name, line.id, product.display_name))
                    continue

                secondary_uom = (
                    line.product_uop or product.uop_id or
                    product.uom_po_id or line.product_uom
                )
                uses_configured_uop = bool(
                    product.uop_id and secondary_uom == product.uop_id
                )
                coeff = product.uop_coeff if uses_configured_uop else 1.0
                if float_compare(coeff, 0.0, precision_digits=6) <= 0:
                    blocked.append(_(
                        '%s, línea %s (%s): el coeficiente de la unidad '
                        'secundaria debe ser mayor que cero.'
                    ) % (order.display_name, line.id, product.display_name))
                    continue

                expected_uop_qty = line.product_qty * coeff
                expected_uop_price = line.price_unit / coeff
                qty_is_wrong = float_compare(
                    line.product_uop_qty, expected_uop_qty,
                    precision_digits=6,
                ) != 0
                price_is_wrong = float_compare(
                    line.price_unit_uop, expected_uop_price,
                    precision_digits=6,
                ) != 0
                uop_is_wrong = line.product_uop != secondary_uom

                if not (qty_is_wrong or price_is_wrong or uop_is_wrong):
                    reports[order.id]['already_ok'] += 1
                    continue

                # For received-quantity products, independently verify that
                # qty_received agrees with completed linked stock moves.  The
                # action must never "repair" physical inventory quantities.
                if product.purchase_method == 'receive':
                    done_moves = line.move_ids.filtered(
                        lambda move: move.state == 'done' and
                        move.product_id == product
                    )
                    stock_qty = 0.0
                    for move in done_moves:
                        move_qty = move.product_uom._compute_quantity(
                            move.product_uom_qty, line.product_uom
                        )
                        if move.location_dest_id.usage == 'supplier':
                            if move.to_refund:
                                stock_qty -= move_qty
                        elif not (
                            move.origin_returned_move_id._is_dropshipped() and
                            not move._is_dropshipped_returned()
                        ):
                            stock_qty += move_qty

                    if float_compare(
                            stock_qty, line.qty_received,
                            precision_rounding=rounding) != 0:
                        blocked.append(_(
                            '%s, línea %s (%s): la cantidad recibida (%s) '
                            'no coincide con los movimientos terminados (%s).'
                        ) % (
                            order.display_name, line.id, product.display_name,
                            line.qty_received, stock_qty,
                        ))
                        continue

                vals = {}
                changes = []
                if uop_is_wrong:
                    vals['product_uop'] = secondary_uom.id
                    changes.append(_('unidad secundaria: vacía → %s') % secondary_uom.display_name)
                if qty_is_wrong:
                    vals['product_uop_qty'] = expected_uop_qty
                    changes.append(_(
                        'cantidad UoP: %s → %s'
                    ) % (line.product_uop_qty, expected_uop_qty))
                if price_is_wrong:
                    vals['price_unit_uop'] = expected_uop_price
                    changes.append(_(
                        'precio UoP: %s → %s'
                    ) % (line.price_unit_uop, expected_uop_price))

                repair_plan.append((line, vals))
                reports[order.id]['repaired'].append((line, changes))

        if blocked:
            raise UserError(_(
                'No se ha modificado ningún dato porque se detectaron '
                'situaciones que requieren revisión manual:\n\n%s'
            ) % '\n'.join(blocked))

        for line, vals in repair_plan:
            line.write(vals)

        repaired_count = 0
        for order in self:
            report = reports[order.id]
            repaired_count += len(report['repaired'])
            details = []
            for line, changes in report['repaired']:
                details.append('<li>%s (línea %s): %s</li>' % (
                    html_escape(line.name or line.product_id.display_name),
                    line.id,
                    html_escape('; '.join(changes)),
                ))
            if details:
                detail_html = '<ul>%s</ul>' % ''.join(details)
            else:
                detail_html = '<p>%s</p>' % _(
                    'No se encontraron líneas pendientes que necesitaran corrección.'
                )
            order.message_post(body=(
                '<p><strong>%s</strong></p>%s'
                '<p>%s: %s. %s: %s.</p>'
            ) % (
                _('Revisión de datos de facturación UoP'), detail_html,
                _('Líneas ya correctas'), report['already_ok'],
                _('Líneas sin cantidad pendiente'), report['not_pending'],
            ))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Revisión completada'),
                'message': _(
                    '%s línea(s) corregida(s). Ya puede volver a usar Crear factura.'
                ) % repaired_count,
                'type': 'success',
                'sticky': repaired_count == 0,
                'next': {'type': 'ir.actions.client', 'tag': 'reload'},
            },
        }


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.multi
    @api.depends('product_id')
    def _compute_product_uop_coeff(self):
        for record_id in self:
            if record_id.product_id and record_id.product_uop == record_id.product_id.uop_id:
                record_id.product_uop_coeff = record_id.product_id.uop_coeff
            else:
                record_id.product_uop_coeff = 1.0

    product_uop_qty = fields.Float(
        string=_('Quantity (UoP)'),
        readonly=True,
        digits=dp.get_precision('Product UoP')
    )

    product_uop = fields.Many2one(
        comodel_name='uom.uom',
        string=_('Product UoP')
    )

    product_uop_coeff = fields.Float(
        comodel_name='uom.uom',
        string=_('UoM -> UoP Coeff'),
        digits=dp.get_precision('Product UoP'),
        compute=_compute_product_uop_coeff
    )

    price_unit_uop = fields.Float(
        string=_('UoP Unit Price'),
        readonly=True,
        digits=dp.get_precision('Product Price')
    )

    @api.onchange('price_unit')
    def onchange_price_unit(self):
        if self.product_id:
            self.price_unit_uop = self.price_unit / self.product_id.uop_coeff

    @api.onchange('price_unit_uop')
    def onchange_price_unit_uop(self):
        if self.product_id:
            self.price_unit = self.price_unit_uop * self.product_id.uop_coeff

    @api.onchange('product_uop_qty')
    def onchange_product_uop_qty(self):
        if self.product_id:
            self.product_qty = self.product_uop_qty / self.product_id.uop_coeff

    @api.onchange('product_qty')
    def onchange_product_qty(self):
        if self.product_id:
            self.product_uop_qty = self.product_qty * self.product_id.uop_coeff

    @api.onchange('product_uop')
    def onchange_product_uop(self):
        if self.product_uop == self.product_id.uop_id:
            self.product_uop_coeff = self.product_id.uop_coeff
        else:
            self.product_uop_coeff = 1.0

    @api.onchange('product_id')
    def onchange_product_id(self):
        res = super(PurchaseOrderLine, self).onchange_product_id()

        if bool(self.product_id):
            self.product_uom = self.product_id.uom_id.id
            self.product_uop = self.product_id.uom_po_id.id or self.product_id.uop_id.id
            self.name = self.product_id.description_purchase_product or ''
        else:
            self.product_uom = False
            self.product_uop = False

        # Buscar el último precio de compra del producto
        last_purchase = self.env['product.purchase.history'].search([
            ('product_id', '=', self.product_id.id)
        ], order='date_order desc', limit=1)
        if last_purchase:
            self.price_unit = last_purchase.price_unit
            logger.info(f"[ONCHANGE] Asignado precio_unit={last_purchase.price_unit} para product_id={self.product_id.id}")

        return res

#
# class AccountInvoice(models.Model):
#     _inherit = 'account.invoice'
#
#     @api.multi
#     def action_invoice_re_open(self):
#         pedidos = self.env['purchase.order'].search([])
#         for pedido in pedidos:
#             for linea in pedido.order_line:
#                 vals = self.write({'purchase_unit_uop': linea.price_unit,
#                                    'product_uop': linea.product_uom,
#                                    'product_uop_qty': linea.product_qty
#                                })
#
#         return vals
