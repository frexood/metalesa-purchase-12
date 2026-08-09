from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import SavepointCase


class TestPurchaseUopRepair(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestPurchaseUopRepair, cls).setUpClass()
        cls.env.user.write({
            'groups_id': [(4, cls.env.ref('purchase.group_purchase_manager').id)],
        })
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')
        cls.partner = cls.env['res.partner'].create({
            'name': 'Proveedor prueba reparación UoP',
            'supplier': True,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Producto prueba reparación UoP',
            'type': 'service',
            'purchase_method': 'purchase',
            'purchase_ok': True,
            'uom_id': cls.uom_unit.id,
            'uom_po_id': cls.uom_unit.id,
            'uop_coeff': 1.0,
        })

    def _create_order_and_line(self):
        order = self.env['purchase.order'].create({
            'partner_id': self.partner.id,
            'state': 'purchase',
        })
        line = self.env['purchase.order.line'].create({
            'order_id': order.id,
            'product_id': self.product.id,
            'name': self.product.name,
            'product_qty': 4.0,
            'qty_received': 4.0,
            'product_uom': self.uom_unit.id,
            'price_unit': 12.5,
            'date_planned': fields.Datetime.now(),
        })
        return order, line

    def test_repair_missing_values_is_idempotent(self):
        order, line = self._create_order_and_line()
        self.assertFalse(line.product_uop)
        self.assertEqual(line.product_uop_qty, 0.0)
        self.assertEqual(line.price_unit_uop, 0.0)

        order.action_repair_uop_before_invoice()
        self.assertEqual(line.product_uop, self.uom_unit)
        self.assertEqual(line.product_uop_qty, 4.0)
        self.assertEqual(line.price_unit_uop, 12.5)

        values_after_first_run = (
            line.product_uop.id,
            line.product_uop_qty,
            line.price_unit_uop,
        )
        order.action_repair_uop_before_invoice()
        self.assertEqual(values_after_first_run, (
            line.product_uop.id,
            line.product_uop_qty,
            line.price_unit_uop,
        ))

    def test_does_not_touch_line_without_pending_quantity(self):
        order, line = self._create_order_and_line()
        line.product_qty = 0.0

        order.action_repair_uop_before_invoice()
        self.assertFalse(line.product_uop)
        self.assertEqual(line.product_uop_qty, 0.0)
        self.assertEqual(line.price_unit_uop, 0.0)

    def test_rejects_unconfirmed_order(self):
        order, line = self._create_order_and_line()
        order.state = 'draft'

        with self.assertRaises(UserError):
            order.action_repair_uop_before_invoice()
        self.assertFalse(line.product_uop)

    def test_rejects_unsafe_ordered_quantity_case(self):
        order, line = self._create_order_and_line()
        line.qty_received = 2.0

        with self.assertRaises(UserError):
            order.action_repair_uop_before_invoice()
        self.assertFalse(line.product_uop)
