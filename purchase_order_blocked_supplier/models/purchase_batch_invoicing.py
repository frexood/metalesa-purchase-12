# Copyright 2016 Jairo Llopis <jairo.llopis@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from logging import getLogger

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = getLogger(__name__)


class PurchaseBatchInvoicing(models.TransientModel):
    _inherit = "purchase.batch_invoicing"

    @api.multi
    def action_batch_invoice(self):
        if self.purchase_order_ids and self.purchase_order_ids[0].partner_id:
            if self.purchase_order_ids[0].partner_id.blocked_supplier:
                raise ValidationError(_("PROVEEDOR BLOQUEADO. PREGUNTA A CONTABILIDAD O CALIDAD"))
        return super(PurchaseBatchInvoicing, self).action_batch_invoice()
