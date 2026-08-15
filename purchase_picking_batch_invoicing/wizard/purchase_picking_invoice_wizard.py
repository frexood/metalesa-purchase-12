# -*- coding: utf-8 -*-

from collections import defaultdict

from psycopg2 import OperationalError

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero


class PurchasePickingInvoiceWizard(models.TransientModel):
    _name = "purchase.picking.invoice.wizard"
    _description = "Create Vendor Bills from Purchase Receipts"

    picking_ids = fields.Many2many(
        comodel_name="stock.picking",
        string="Purchase Receipts",
        required=True,
        readonly=True,
        default=lambda self: self._default_picking_ids(),
    )
    grouping = fields.Selection(
        selection=[
            ("compatible", "Consolidate compatible receipts into one bill"),
            ("picking", "Create one bill per receipt"),
        ],
        string="Grouping",
        required=True,
        default="compatible",
        help=(
            "Consolidate compatible receipts: creates a single vendor bill when "
            "company, vendor, currency, fiscal position and payment terms match.\n"
            "Receipts with different conditions are placed in separate vendor "
            "bills.\n"
            "Create one bill per receipt: creates an independent vendor bill for "
            "each selected receipt."
        ),
    )

    @api.model
    def _default_picking_ids(self):
        if self.env.context.get("active_model") != "stock.picking":
            return False
        return self.env.context.get("active_ids", [])

    def _lock_moves(self, moves):
        """Serialize invoicing of the selected moves and re-read their links."""
        if not moves:
            return
        try:
            with self.env.cr.savepoint():
                self.env.cr.execute(
                    "SELECT id FROM stock_move WHERE id IN %s FOR UPDATE NOWAIT",
                    [tuple(moves.ids)],
                )
        except OperationalError:
            raise UserError(_(
                "One of the selected receipts is being invoiced by another user. "
                "Please try again when that operation has finished."
            ))
        moves.invalidate_cache(["purchase_invoice_line_ids"])

    def _get_purchase_moves(self):
        pickings = self.picking_ids
        if not pickings:
            raise UserError(_("Select at least one purchase receipt."))

        invalid_pickings = pickings.filtered(
            lambda picking: (
                picking.state != "done" or
                picking.picking_type_id.code != "incoming" or
                picking.location_id.usage != "supplier"
            )
        )
        if invalid_pickings:
            raise UserError(_(
                "Only completed vendor receipts can be invoiced. "
                "Invalid receipts: %s"
            ) % ", ".join(invalid_pickings.mapped("name")))

        moves = pickings.mapped("move_lines").filtered(
            lambda move: (
                move.state == "done" and
                not move.scrapped and
                move.location_id.usage == "supplier" and
                move.location_dest_id.usage != "supplier" and
                not float_is_zero(
                    move.product_uom_qty,
                    precision_rounding=move.product_uom.rounding,
                )
            )
        )
        moves_without_purchase = moves.filtered(lambda move: not move.purchase_line_id)
        if moves_without_purchase:
            raise UserError(_(
                "All moves in the selected receipts must come from a purchase "
                "order. Moves without a purchase order line: %s"
            ) % ", ".join(moves_without_purchase.mapped("display_name")))
        if not moves:
            raise UserError(_(
                "The selected receipts do not contain billable purchase moves."
            ))
        return moves

    def _validate_moves(self, moves):
        self._lock_moves(moves)

        already_invoiced = moves.filtered(lambda move: any(
            line.invoice_id.state != "cancel"
            for line in move.purchase_invoice_line_ids
        ))
        if already_invoiced:
            raise UserError(_(
                "Some moves in the selected receipts are already included in a "
                "non-cancelled vendor bill: %s"
            ) % ", ".join(already_invoiced.mapped("display_name")))

        selected_by_line = defaultdict(float)
        for move in moves:
            line = move.purchase_line_id
            selected_by_line[line] += move.product_uom._compute_quantity(
                move.product_uom_qty,
                line.product_uom,
                rounding_method="HALF-UP",
            )

        for line, selected_qty in selected_by_line.items():
            if line.product_id.purchase_method == "purchase":
                billable_qty = line.product_qty
            else:
                billable_qty = line.qty_received
            remaining_qty = billable_qty - line.qty_invoiced
            if float_compare(
                selected_qty,
                remaining_qty,
                precision_rounding=line.product_uom.rounding,
            ) > 0:
                raise UserError(_(
                    "The selected quantity %(selected)s exceeds the remaining "
                    "billable quantity %(remaining)s on purchase order "
                    "%(order)s for product %(product)s."
                ) % {
                    "selected": selected_qty,
                    "remaining": max(remaining_qty, 0.0),
                    "order": line.order_id.name,
                    "product": line.product_id.display_name,
                })

    def _compatibility_key(self, move):
        order = move.purchase_line_id.order_id
        key = (
            order.company_id.id,
            order.partner_id.id,
            order.currency_id.id,
            order.fiscal_position_id.id,
            order.payment_term_id.id,
        )
        if self.grouping == "picking":
            key += (move.picking_id.id,)
        return key

    def _group_moves(self, moves):
        groups = defaultdict(lambda: self.env["stock.move"])
        for move in moves:
            groups[self._compatibility_key(move)] |= move
        return groups.values()

    def _prepare_invoice(self, moves):
        orders = moves.mapped("purchase_line_id.order_id")
        order = orders[0]
        Invoice = self.env["account.invoice"].with_context(
            default_type="in_invoice",
            type="in_invoice",
            default_company_id=order.company_id.id,
            company_id=order.company_id.id,
            force_company=order.company_id.id,
        )
        requested_defaults = [
            "type", "company_id", "currency_id", "journal_id", "account_id",
            "payment_term_id", "fiscal_position_id", "date_invoice", "user_id",
        ]
        values = Invoice.default_get(requested_defaults)
        values.update({
            "type": "in_invoice",
            "partner_id": order.partner_id.id,
            "company_id": order.company_id.id,
            "currency_id": order.currency_id.id,
            "payment_term_id": order.payment_term_id.id,
            "fiscal_position_id": order.fiscal_position_id.id,
            "origin": ", ".join(orders.mapped("name")),
        })
        invoice = Invoice.new(values)
        invoice._onchange_partner_id()
        values = invoice._convert_to_write(invoice._cache)
        # Header compatibility values must come from the purchase order, not
        # from partner defaults potentially applied by the onchange.
        values.update({
            "type": "in_invoice",
            "partner_id": order.partner_id.id,
            "company_id": order.company_id.id,
            "currency_id": order.currency_id.id,
            "payment_term_id": order.payment_term_id.id,
            "fiscal_position_id": order.fiscal_position_id.id,
            "origin": ", ".join(orders.mapped("name")),
        })
        return Invoice.create(values)

    def _selected_quantity(self, moves, purchase_line):
        return sum(
            move.product_uom._compute_quantity(
                move.product_uom_qty,
                purchase_line.product_uom,
                rounding_method="HALF-UP",
            )
            for move in moves
        )

    def _prepare_invoice_line(self, invoice, purchase_line, picking, moves):
        selected_qty = self._selected_quantity(moves, purchase_line)
        values = invoice._prepare_invoice_line_from_po_line(purchase_line)
        values.update({
            "invoice_id": invoice.id,
            "quantity": selected_qty,
            "uom_id": purchase_line.product_uom.id,
            "name": "%s - %s: %s" % (
                picking.name,
                purchase_line.order_id.name,
                purchase_line.name,
            ),
            "purchase_stock_move_ids": [(6, 0, moves.ids)],
        })

        # Preserve Metalesa's secondary purchase unit while basing it on this
        # receipt instead of cumulative qty_received on the purchase line.
        if "cantidad_recibida" in self.env["account.invoice.line"]._fields:
            ratio = (
                purchase_line.product_uop_qty / purchase_line.product_qty
                if purchase_line.product_qty else 0.0
            )
            secondary_qty = selected_qty * ratio
            values["cantidad_recibida"] = secondary_qty
            values["product_uop_qty"] = purchase_line.product_uop_qty
            secondary_price = purchase_line.price_unit_uop
            if float_is_zero(secondary_price, precision_digits=6) and ratio:
                secondary_price = purchase_line.price_unit / ratio
            values["price_unit_uop"] = secondary_price
            values["product_uop_id"] = purchase_line.product_uop.id
            if purchase_line.product_uop and not float_is_zero(
                ratio, precision_digits=6
            ):
                values.update({
                    "quantity": secondary_qty,
                    "uom_id": purchase_line.product_uop.id,
                    "price_unit": secondary_price,
                })
        return values

    def _create_invoice_lines(self, invoice, moves):
        InvoiceLine = self.env["account.invoice.line"].with_context(
            preserve_purchase_receipt_quantities=True
        )
        pickings = moves.mapped("picking_id")
        for picking in pickings:
            picking_moves = moves.filtered(lambda move: move.picking_id == picking)
            for purchase_line in picking_moves.mapped("purchase_line_id"):
                line_moves = picking_moves.filtered(
                    lambda move: move.purchase_line_id == purchase_line
                )
                values = self._prepare_invoice_line(
                    invoice, purchase_line, picking, line_moves
                )
                InvoiceLine.create(values)

    @api.multi
    def action_create_invoices(self):
        self.ensure_one()
        moves = self._get_purchase_moves()
        self._validate_moves(moves)

        invoices = self.env["account.invoice"]
        for grouped_moves in self._group_moves(moves):
            partners = grouped_moves.mapped("purchase_line_id.order_id.partner_id")
            blocked = partners.filtered(
                lambda partner: (
                    "blocked_supplier" in partner._fields and
                    partner.blocked_supplier
                )
            )
            if blocked:
                raise UserError(_(
                    "Vendor blocked. Contact Accounting or Quality: %s"
                ) % ", ".join(blocked.mapped("display_name")))

            invoice = self._prepare_invoice(grouped_moves)
            self._create_invoice_lines(invoice, grouped_moves)
            invoice.compute_taxes()
            invoices |= invoice

        if not invoices:
            raise UserError(_(
                "No vendor bill could be created."
            ))

        action = self.env.ref("account.action_vendor_bill_template").read()[0]
        if len(invoices) == 1:
            action["views"] = [
                (self.env.ref("account.invoice_supplier_form").id, "form")
            ]
            action["res_id"] = invoices.id
        else:
            action["domain"] = [("id", "in", invoices.ids)]
        return action
