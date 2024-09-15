# Copyright 2016 Jairo Llopis <jairo.llopis@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from logging import getLogger

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = getLogger(__name__)


class PurchaseBatchInvoicing(models.TransientModel):
    _inherit = "purchase.batch_invoicing"

    grouping = fields.Selection(
        selection=[
            ("id", "Purchase Order"),
            ("partner_id", "Vendor"),
        ],
        required=True,
        default="partner_id",
        help="Make one invoice for each...",
    )

