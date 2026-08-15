Purchase Picking Batch Invoicing
================================

Spanish end-user guide: `GUIA_USUARIO.md <GUIA_USUARIO.md>`_.

Creates vendor bills exclusively from the completed purchase receipts selected
by the user. Compatible receipts can be grouped while preserving links from the
bill lines to purchase order lines, stock moves and receipts.

Usage
-----

#. Open the inventory transfers list and select completed supplier receipts.
#. Run ``Action > Create Vendor Bills from Receipts``.
#. Choose whether compatible receipts are grouped or one bill is created per
   receipt.
#. Confirm the wizard. The resulting bills remain in draft.

Receipts are grouped only when company, vendor, currency, fiscal position and
payment terms match. A completed stock move cannot be included in two active
vendor bills. Cancelling or deleting its bill makes the receipt invoiceable
again.
