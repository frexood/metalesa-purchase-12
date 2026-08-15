# -*- coding: utf-8 -*-

from datetime import datetime

from odoo.addons.account.tests.account_test_classes import AccountingTestCase
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


@tagged("post_install", "-at_install")
class TestPurchasePickingInvoicing(AccountingTestCase):

    def setUp(self):
        super(TestPurchasePickingInvoicing, self).setUp()
        self.vendor = self.env["res.partner"].create({
            "name": "Test receipt invoicing vendor",
            "supplier": True,
        })
        self.product = self.env["product.product"].create({
            "name": "Test receipt invoicing product",
            "purchase_method": "receive",
            "type": "product",
        })
        self.company = self.env.user.company_id
        self.warehouse = self.env["stock.warehouse"].search([
            ("company_id", "=", self.company.id),
        ], limit=1)
        self.picking_type = self.warehouse.in_type_id
        self.supplier_location = self.vendor.property_stock_supplier
        self.stock_location = self.warehouse.lot_stock_id

    def _create_order(self, quantity):
        order = self.env["purchase.order"].create({
            "partner_id": self.vendor.id,
            "order_line": [(0, 0, {
                "name": self.product.display_name,
                "product_id": self.product.id,
                "product_qty": quantity,
                "product_uom": self.product.uom_po_id.id,
                "price_unit": 10.0,
                "date_planned": datetime.today().strftime(
                    DEFAULT_SERVER_DATETIME_FORMAT
                ),
            })],
        })
        # Avoid creating a standard aggregate receipt: these tests create the
        # individual completed receipts explicitly below.
        order.write({"state": "purchase"})
        return order

    def _create_done_receipt(self, line, quantity, suffix):
        picking = self.env["stock.picking"].create({
            "name": "TEST-RECEIPT-%s" % suffix,
            "partner_id": line.order_id.partner_id.id,
            "picking_type_id": self.picking_type.id,
            "location_id": self.supplier_location.id,
            "location_dest_id": self.stock_location.id,
            "origin": line.order_id.name,
        })
        move = self.env["stock.move"].create({
            "name": line.name,
            "product_id": line.product_id.id,
            "product_uom_qty": quantity,
            "product_uom": line.product_uom.id,
            "location_id": self.supplier_location.id,
            "location_dest_id": self.stock_location.id,
            "picking_id": picking.id,
            "picking_type_id": self.picking_type.id,
            "purchase_line_id": line.id,
            "company_id": self.company.id,
            "state": "done",
        })
        line._update_received_qty()
        picking._compute_state()
        picking.invalidate_cache(["state"])
        return picking, move

    def _invoice_pickings(self, pickings):
        wizard = self.env["purchase.picking.invoice.wizard"].with_context(
            active_model="stock.picking",
            active_ids=pickings.ids,
        ).create({})
        action = wizard.action_create_invoices()
        if action.get("res_id"):
            return self.env["account.invoice"].browse(action["res_id"])
        return self.env["account.invoice"].search(action["domain"])

    def test_selected_receipts_only(self):
        order = self._create_order(45.0)
        line = order.order_line
        receipt_1, move_1 = self._create_done_receipt(line, 10.0, "1")
        receipt_2, move_2 = self._create_done_receipt(line, 20.0, "2")
        receipt_3, move_3 = self._create_done_receipt(line, 15.0, "3")

        invoice = self._invoice_pickings(receipt_1 | receipt_3)

        self.assertEqual(len(invoice), 1)
        self.assertEqual(sum(invoice.invoice_line_ids.mapped("quantity")), 25.0)
        self.assertEqual(
            set(invoice.invoice_line_ids.mapped("purchase_stock_move_ids").ids),
            {move_1.id, move_3.id},
        )
        self.assertNotIn(move_2, invoice.invoice_line_ids.mapped(
            "purchase_stock_move_ids"
        ))
        self.assertEqual(line.qty_invoiced, 25.0)

        with self.assertRaises(UserError):
            self._invoice_pickings(receipt_1)

        second_invoice = self._invoice_pickings(receipt_2)
        self.assertEqual(
            sum(second_invoice.invoice_line_ids.mapped("quantity")), 20.0
        )
        self.assertEqual(line.qty_invoiced, 45.0)

    def test_different_orders_same_vendor_are_grouped(self):
        order_1 = self._create_order(8.0)
        order_2 = self._create_order(12.0)
        receipt_1, move_1 = self._create_done_receipt(
            order_1.order_line, 8.0, "A"
        )
        receipt_2, move_2 = self._create_done_receipt(
            order_2.order_line, 12.0, "B"
        )

        invoice = self._invoice_pickings(receipt_1 | receipt_2)

        self.assertEqual(len(invoice), 1)
        self.assertEqual(
            set(invoice.invoice_line_ids.mapped("purchase_line_id.order_id").ids),
            {order_1.id, order_2.id},
        )
        self.assertEqual(
            set(invoice.invoice_line_ids.mapped("purchase_stock_move_ids").ids),
            {move_1.id, move_2.id},
        )
