# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class PurchaseReceiveNotification(models.Model):
    _name = 'purchase.receive.notification'
    _description = 'Notificación de recepción de materiales'
    _inherit = ['mail.thread']

    picking_id = fields.Many2one('stock.picking', string='Recepción', required=True, ondelete='cascade', tracking=True)
    purchase_id = fields.Many2one('purchase.order', string='Orden de Compra')
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('sent', 'Correo Enviado')
    ], string='Estado', default='draft', tracking=True)

    analytic_account_id = fields.Many2one('account.analytic.account', string='Cuenta Analítica')
    analytic_account_parent_id = fields.Many2one('account.analytic.account', string='Proyecto')
    analytic_user_id = fields.Many2one('res.users', string='Gestor del Proyecto')
    project_id = fields.Many2one('project.project', string='ID del Proyecto')


    project_name = fields.Char(string='Nombre del Proyecto')
    email_table_html = fields.Text(string="Tabla HTML", compute='_compute_email_table', store=False)

    purchase_url = fields.Char(string='URL Orden de Compra', compute='_compute_urls', store=True)
    picking_url = fields.Char(string='URL Albarán', compute='_compute_urls', store=True)

    @api.depends('purchase_id', 'picking_id')
    def _compute_urls(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for rec in self:
            rec.purchase_url = ''
            rec.picking_url = ''
            if rec.purchase_id:
                rec.purchase_url = f'{base_url}/web#id={rec.purchase_id.id}&model=purchase.order&view_type=form'
            if rec.picking_id:
                rec.picking_url = f'{base_url}/web#id={rec.picking_id.id}&model=stock.picking&view_type=form'

    @api.model
    def create(self, vals):
        rec = super(PurchaseReceiveNotification, self).create(vals)
        rec._set_analytic_fields()  
        rec.send_notification_email() 

        return rec

    def _set_analytic_fields(self):
        for rec in self:
            picking = rec.picking_id
            analytic_account = None
            parent_account = None
            purchase = picking.purchase_id if picking else False

            project_id = False
            project_name = ''
            delineante = False

            if picking:
                for move in picking.move_lines:
                    if move.analytic_account_id:
                        analytic_account = move.analytic_account_id
                        parent_account = analytic_account.parent_id

                        # Extraer nombre del proyecto desde el nombre de la cuenta analítica
                        full_name = analytic_account.name
                        if full_name and '/' in full_name:
                            project_name = full_name.split('/')[0].strip()
                        else:
                            project_name = full_name.strip()

                        if parent_account:
                        # Buscar en el modelo project.project por nombre exacto
                            project = self.env['project.project'].search([
                                ('name', '=', parent_account.name)
                            ], limit=1)

                            if project:
                                project_id = project.id
                                delineante = project.delineante.id if project.delineante else False
                        break

            rec.write({
                'analytic_account_id': analytic_account.id if analytic_account else False,
                'analytic_account_parent_id': parent_account.id if parent_account else False,
                'project_name': project_name,
                'project_id': project_id,
                'analytic_user_id': delineante,
                'purchase_id': purchase.id if purchase else False,
            })


    @api.depends('picking_id')
    def _compute_email_table(self):
        for rec in self:
            rows = ""
            for move in rec.picking_id.move_lines:
                if move.purchase_line_id:
                    qty_pedida = move.purchase_line_id.product_qty
                    qty_recibida = move.quantity_done
                    qty_total = sum(
                        m.quantity_done for m in move.purchase_line_id.move_ids.filtered(lambda m: m.state == 'done')
                    )
                    rows += '''
                        <tr>
                            <td>%s</td>
                            <td>%.2f</td>
                            <td>%.2f</td>
                            <td>%.2f</td>
                        </tr>
                    ''' % (
                        move.product_id.display_name,
                        qty_pedida,
                        qty_recibida,
                        qty_total
                    )
            if not rows:
                rows = '<tr><td colspan="4">No se encontraron productos recibidos.</td></tr>'
            rec.email_table_html = '''
                <table border="1" cellspacing="0" cellpadding="5" style="border-collapse: collapse; width: 100%%;">
                    <thead style="background-color: #f0f0f0;">
                        <tr>
                            <th>Producto</th>
                            <th>Cant. Pedida</th>
                            <th>Recibido (última)</th>
                            <th>Total Recibido</th>
                        </tr>
                    </thead>
                    <tbody>
                        %s
                    </tbody>
                </table>
            ''' % rows



    def send_notification_email(self):
        template = self.env.ref(
            'purchase_automate_notifications.template_receive_material_email',
            raise_if_not_found=False
        )
        if not template:
            raise UserError("La plantilla de correo no está definida correctamente.")

        config = self.env['purchase.notification.config'].search([], limit=1)

        for rec in self:
            if not rec.picking_id:
                continue

            # Excluir porfolio
            if rec.purchase_id and rec.purchase_id.porfolio:
                _logger.info("No se envía correo: la orden está marcada como porfolio: %s", rec.purchase_id.name)
                continue

            # Excluir productos tipo transporte
            has_transport = any(
                'transporte' in (move.product_id.display_name or '').lower()
                for move in rec.picking_id.move_lines if move.product_id
            )
            if has_transport:
                _logger.info("No se envía correo: contiene producto transporte: %s", rec.picking_id.name)
                continue

            # Obtener destinatario principal: Gestor del Proyecto
            user = rec.analytic_user_id
            email_to = user.employee_ids and user.employee_ids[0].work_email or False

            if not email_to:
                _logger.warning("Gestor del Proyecto no tiene correo configurado. Se omite el envío.")
                continue

            # Obtener copia: todos los empleados definidos en config (si existe)
            email_cc = ''
            if config and config.employee_ids:
                email_cc = ','.join(
                    emp.work_email for emp in config.employee_ids if emp.work_email
                )

            _logger.info("Enviando correo a: %s | CC: %s", email_to, email_cc)

            template.send_mail(rec.id, force_send=True, email_values={
                'email_to': email_to,
                'email_cc': email_cc,
                'email_from': 'recepciones@metalesa.com',
            })

            rec.state = 'sent'
