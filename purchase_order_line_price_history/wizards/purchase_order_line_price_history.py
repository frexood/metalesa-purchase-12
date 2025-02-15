# Copyright 2019 Tecnativa - Ernesto Tejeda
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class purchaseOrderLinePriceHistory(models.TransientModel):
    _name = "purchase.order.line.price.history"
    _description = "purchase order line price history"

    @api.model
    def _default_partner_id(self):
        line_id = self.env.context.get("active_id")
        return self.env['purchase.order.line'].browse(line_id).partner_id.id

    purchase_order_line_id = fields.Many2one(
        comodel_name='purchase.order.line',
        string='purchase order line',
        default=lambda self: self.env.context.get("active_id"),
    )
    product_id = fields.Many2one(
        related="purchase_order_line_id.product_id",
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        default=_default_partner_id,
    )
    line_ids = fields.One2many(
        comodel_name="purchase.order.line.price.history.line",
        inverse_name="history_id",
        string="History lines",
        readonly=True,
    )
    include_quotations = fields.Boolean(
        string="Include quotations",
        help="Include quotations lines in the purchase history",
    )
    include_commercial_partner = fields.Boolean(
        string="Include commercial entity",
        default=True,
        help="Include commercial entity and its contacts in the purchase history"
    )

    @api.onchange("partner_id", "include_quotations",
                  "include_commercial_partner")
    def _onchange_partner_id(self):
        self.line_ids = False
        states = ["purchase", "done"]
        if self.include_quotations:
            states += ["draft", "sent"]
        domain = [
            ("product_id", "=", self.product_id.id),
            ("state", "in", states),
        ]
        if self.partner_id:
            if self.include_commercial_partner:
                domain += [("partner_id", "child_of",
                            self.partner_id.commercial_partner_id.ids)]
            else:
                domain += [
                    ("partner_id", "child_of", self.partner_id.ids)]

        vals = []
        order_lines = self.env['purchase.order.line'].search(domain, limit=20)
        order_lines -= self.purchase_order_line_id
        for order_line in order_lines:
            vals.append((0, False, {
                'purchase_order_line_id': order_line.id,
                'history_purchase_order_line_id': self.purchase_order_line_id,
            }))
        self.line_ids = vals


class PurchaseOrderLinePriceHistoryline(models.TransientModel):
    _name = "purchase.order.line.price.history.line"
    _description = "purchase order line price history line"

    history_id = fields.Many2one(
        comodel_name="purchase.order.line.price.history",
        string="History",
    )
    history_purchase_order_line_id = fields.Many2one(
        comodel_name='purchase.order.line',
        string="history purchase order line",
    )
    purchase_order_line_id = fields.Many2one(
        comodel_name='purchase.order.line',
        string='purchase order line',
    )
    order_id = fields.Many2one(
        related="purchase_order_line_id.order_id",
    )
    partner_id = fields.Many2one(
        related="purchase_order_line_id.partner_id",
    )
    purchase_order_date_order = fields.Datetime(
        related="purchase_order_line_id.order_id.date_order",
    )
    product_uom_qty = fields.Float(
        related="purchase_order_line_id.product_uom_qty",
    )
    price_unit = fields.Float(
        related="purchase_order_line_id.price_unit",
    )

    @api.multi
    def action_set_price(self):
        self.ensure_one()
        self.history_purchase_order_line_id.price_unit = self.price_unit
