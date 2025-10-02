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
            purchase = rec.purchase_id or (rec.picking_id.purchase_id if rec.picking_id else False)

            analytic_account = None
            parent_account = None
            project_id = False
            project_name = ''
            delineante = False

            # ---------- Solo desde líneas de la OC ----------
            if purchase:
                # Buscar la primera línea que tenga cuenta analítica
                po_line = next((l for l in purchase.order_line if l.account_analytic_id), None)
                if po_line and po_line.account_analytic_id:
                    analytic_account = po_line.account_analytic_id
                    parent_account = analytic_account.parent_id

            # ---------- Nombre del proyecto ----------
            if analytic_account:
                full_name = analytic_account.name or ''
                if '/' in full_name:
                    project_name = full_name.split('/')[0].strip()
                else:
                    project_name = full_name.strip()

            # ---------- Localizar el project.project ----------
            project = False
            if parent_account:
                project = self.env['project.project'].search([
                    ('analytic_account_id', '=', parent_account.id)
                ], limit=1)

            if not project and analytic_account:
                project = self.env['project.project'].search([
                    ('analytic_account_id', '=', analytic_account.id)
                ], limit=1)

            if project:
                project_id = project.id
                delineante = project.delineante.id if getattr(project, 'delineante', False) else False

            # ---------- Escribir campos ----------
            rec.write({
                'analytic_account_id': analytic_account.id if analytic_account else False,
                'analytic_account_parent_id': parent_account.id if parent_account else False,
                'project_name': project_name,
                'project_id': project_id or False,
                'analytic_user_id': delineante or False,
                'purchase_id': purchase.id if purchase else False,
            })


    @api.depends('picking_id')
    def _compute_email_table(self):
        for rec in self:
            rows = ""
            incident_messages = []

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

                # Revisión de campos de calidad por cada move_line
                for move_line in move.move_line_ids:
                    fields_bad = []
                    if move_line.quantity_quality == 'bad':
                        fields_bad.append('CANTIDAD')
                    if move_line.quality == 'bad':
                        fields_bad.append('CALIDAD')
                    if move_line.dimension == 'bad':
                        fields_bad.append('DIMENSIONES')

                    if fields_bad:
                        incident_text = '''
                            EN EL %s, INCIDENCIA EN %s, LA INCIDENCIA ES:  %s.
                        ''' % (
                            move.product_id.display_name,
                            '/'.join(fields_bad),
                            move_line.incidence or 'Sin descripción.'
                        )
                        incident_messages.append(incident_text.strip())

            if not rows:
                rows = '<tr><td colspan="4">No se encontraron productos recibidos.</td></tr>'

            table_html = '''
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

            # Bloque de incidencias si las hay
            if incident_messages:
                incident_block = '''
                    <div style="color: red; font-weight: bold; margin-top: 20px;">
                        DURANTE LA INSPECCIÓN DEL MATERIAL RECIBIDO SE HAN ENCONTRADO LAS SIGUIENTES INCIDENCIAS:
                        <ul style="color: red; font-weight: normal;">
                            %s
                        </ul>
                    </div>
                ''' % ''.join(f'<li>{msg}</li>' for msg in incident_messages)

                table_html += incident_block

            rec.email_table_html = table_html


    def send_notification_email(self):
        template = self.env.ref(
            'purchase_automate_notifications.template_receive_material_email',
            raise_if_not_found=False
        )
        if not template:
            raise UserError("La plantilla de correo no está definida correctamente.")

        config = self.env['purchase.notification.config'].sudo().search([], limit=1)

        for rec in self:
            if not rec.picking_id:
                continue

            if rec.purchase_id and rec.purchase_id.porfolio:
                _logger.info("No se envía correo porque la orden está marcada como porfolio: %s", rec.purchase_id.name)
                continue

            has_transport = any(
                'transporte' in (move.product_id.display_name or '').lower()
                for move in rec.picking_id.move_lines
                if move.product_id
            )
            if has_transport:
                _logger.info("No se envía correo porque contiene producto transporte: %s", rec.picking_id.name)
                continue

            # Buscar email_to desde el empleado (work_email)
            employee = self.env['hr.employee'].sudo().search([('user_id', '=', rec.analytic_user_id.id)], limit=1)
            email_to = employee.work_email if employee and employee.work_email else None

            # --- CC normal desde configuración ---
            config = self.env['purchase.notification.config'].sudo().search([], limit=1)
            email_cc_list = [emp.work_email for emp in config.employee_ids if emp.work_email]

            # --- Validar si hay alguna línea con valores 'bad' ---
            found_bad = False
            for move in rec.picking_id.move_lines:
                for line in move.move_line_ids:
                    if line.dimension == 'bad' or line.quantity_quality == 'bad' or line.quality == 'bad':
                        found_bad = True
                        break
                if found_bad:
                    break

            # Si hay incidencia, añadir a empleados responsables de incidencias
            if found_bad and config:
                bad_emails = [emp.work_email for emp in config.employee_bad_inspection_ids if emp.work_email]
                email_cc_list.extend(bad_emails)

            # Eliminar duplicados y vacíos
            email_cc_list = list(filter(None, set(email_cc_list)))

            if not email_to:
                _logger.warning("Gestor del Proyecto no tiene correo configurado. Se continúa solo con CC.")

            _logger.info("Enviando correo a: %s | CC: %s", email_to or "-", ', '.join(email_cc_list) or "-")

            template.send_mail(rec.id, force_send=True, email_values={
                'email_to': email_to or ','.join(email_cc_list),  # Si no hay email_to, se usa CC como TO
                'email_cc': ','.join(email_cc_list) if email_to else False,
                'email_from': 'recepciones@metalesa.com',
            })

            rec.state = 'sent'
