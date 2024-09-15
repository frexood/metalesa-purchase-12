# -*- coding: utf-8 -*-

from odoo import fields, models, api


class PurchaseOrderExtends(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def create(self, vals):
        tac_ids = self.env['terms.and.conditions'].search([
            ('default', '=', True),("type","=","purchase")
        ])

        if tac_ids:
            comment = vals.get('notes', False)
            if not comment:
                comment = ''
            else:
                comment += '</br>'

            comment += '<ul>'
            for tac_id in tac_ids:
                comment += '<li>{}</li>'.format(tac_id.description)

            vals.update({'notes': comment + '</ul>'})

        return super(PurchaseOrderExtends, self).create(vals)

    def addTermsAndConditions(self):
        return self.env['terms.and.conditions.wizard'].getWizard(
            self.id,
            self._name,
            'notes',
            False
        )
