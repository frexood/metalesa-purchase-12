# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    purchase_receipt_ids = fields.Many2many(
        comodel_name="stock.picking",
        compute="_compute_purchase_receipt_ids",
        string="Purchase Receipts",
        readonly=True,
    )

    @api.depends("invoice_line_ids.purchase_stock_move_ids.picking_id")
    def _compute_purchase_receipt_ids(self):
        for invoice in self:
            invoice.purchase_receipt_ids = invoice.invoice_line_ids.mapped(
                "purchase_stock_move_ids.picking_id"
            )


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    purchase_stock_move_ids = fields.Many2many(
        comodel_name="stock.move",
        relation="purchase_stock_move_invoice_line_rel",
        column1="invoice_line_id",
        column2="move_id",
        string="Purchase Receipt Moves",
        readonly=True,
        copy=False,
    )
    purchase_receipt_id = fields.Many2one(
        comodel_name="stock.picking",
        compute="_compute_purchase_receipt_id",
        string="Purchase Receipt",
        readonly=True,
    )

    @api.depends("purchase_stock_move_ids.picking_id")
    def _compute_purchase_receipt_id(self):
        for line in self:
            pickings = line.purchase_stock_move_ids.mapped("picking_id")
            line.purchase_receipt_id = pickings[:1]

    @api.multi
    def write(self, vals):
        protected_fields = {"quantity", "uom_id", "purchase_line_id"}
        if protected_fields.intersection(vals) and not self.env.context.get(
            "allow_purchase_receipt_quantity_edit"
        ):
            protected_lines = self.filtered("purchase_stock_move_ids")
            changed_lines = protected_lines.filtered(
                lambda line: (
                    "quantity" in vals and float_compare(
                        vals["quantity"],
                        line.quantity,
                        precision_rounding=line.uom_id.rounding,
                    ) != 0
                ) or (
                    "uom_id" in vals and vals["uom_id"] != line.uom_id.id
                ) or (
                    "purchase_line_id" in vals and
                    vals["purchase_line_id"] != line.purchase_line_id.id
                )
            )
            if changed_lines:
                raise UserError(_(
                    "The quantity and unit of measure of an invoice line generated "
                    "from a purchase receipt cannot be modified. Delete the line "
                    "and invoice the receipt again."
                ))
        return super(AccountInvoiceLine, self).write(vals)
