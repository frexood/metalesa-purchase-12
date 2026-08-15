# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools.float_utils import float_compare


class StockMove(models.Model):
    _inherit = "stock.move"

    purchase_invoice_line_ids = fields.Many2many(
        comodel_name="account.invoice.line",
        relation="purchase_stock_move_invoice_line_rel",
        column1="move_id",
        column2="invoice_line_id",
        string="Purchase Bill Lines",
        readonly=True,
        copy=False,
    )


class StockPicking(models.Model):
    _inherit = "stock.picking"

    purchase_invoice_ids = fields.Many2many(
        comodel_name="account.invoice",
        compute="_compute_purchase_invoices",
        string="Vendor Bills",
        readonly=True,
    )
    purchase_invoice_count = fields.Integer(
        compute="_compute_purchase_invoices",
        string="Vendor Bill Count",
    )
    purchase_invoice_state = fields.Selection(
        selection=[
            ("none", "Not Applicable"),
            ("to_invoice", "To Invoice"),
            ("partial", "Partially Invoiced"),
            ("invoiced", "Invoiced"),
        ],
        compute="_compute_purchase_invoices",
        store=True,
        string="Purchase Billing Status",
    )

    @api.depends(
        "move_lines.purchase_invoice_line_ids.invoice_id.state",
        "move_lines.purchase_line_id.qty_invoiced",
        "move_lines.purchase_line_id.qty_received",
        "move_lines.purchase_line_id.product_qty",
        "move_lines.purchase_line_id.product_id.purchase_method",
        "move_lines.state",
        "state",
    )
    def _compute_purchase_invoices(self):
        for picking in self:
            purchase_moves = picking.move_lines.filtered(
                lambda move: move.purchase_line_id and not move.scrapped
            )
            invoice_lines = purchase_moves.mapped("purchase_invoice_line_ids")
            invoices = invoice_lines.mapped("invoice_id")
            active_lines = invoice_lines.filtered(
                lambda line: line.invoice_id.state != "cancel"
            )
            invoiced_moves = active_lines.mapped("purchase_stock_move_ids")
            # Bills created by Odoo's order-based flow have no stock-move
            # link. If the whole PO line is nevertheless billed, consider its
            # receipts billed as well so both invoicing flows remain coherent.
            for move in purchase_moves - invoiced_moves:
                line = move.purchase_line_id
                billable_qty = (
                    line.product_qty
                    if line.product_id.purchase_method == "purchase"
                    else line.qty_received
                )
                if float_compare(
                    line.qty_invoiced,
                    billable_qty,
                    precision_rounding=line.product_uom.rounding,
                ) >= 0:
                    invoiced_moves |= move

            picking.purchase_invoice_ids = invoices
            picking.purchase_invoice_count = len(invoices)
            if picking.state != "done" or not purchase_moves:
                state = "none"
            elif not invoiced_moves:
                state = "to_invoice"
            elif not (purchase_moves - invoiced_moves):
                state = "invoiced"
            else:
                state = "partial"
            picking.purchase_invoice_state = state

    @api.multi
    def action_view_purchase_invoices(self):
        self.ensure_one()
        action = self.env.ref("account.action_vendor_bill_template").read()[0]
        invoices = self.purchase_invoice_ids
        if len(invoices) == 1:
            action["views"] = [
                (self.env.ref("account.invoice_supplier_form").id, "form")
            ]
            action["res_id"] = invoices.id
        else:
            action["domain"] = [("id", "in", invoices.ids)]
        return action
