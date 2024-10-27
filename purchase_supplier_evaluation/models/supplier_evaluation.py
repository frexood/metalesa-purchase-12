# -*- coding: utf-8 -*-

from odoo import fields, models, api, exceptions, _

from datetime import datetime, date

import io
import xlsxwriter
import base64

class ResPartner(models.Model):
    _inherit = 'res.partner'

    sgc = fields.Boolean(
        string=_("SGC"),
    )

    calificacion_proveedor_ids = fields.One2many(
        comodel_name='metalesa.supplier.evaluation',
        inverse_name='supplier_id',
    )
    supplier_qualification_new_ids = fields.One2many(
        comodel_name='metalesa.supplier.evaluation.new',
        inverse_name='supplier_id',
    )

    @api.multi
    def generate_excel(self):
        # Crear un archivo Excel en memoria
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Historico Evaluaciones')

        # Formato de titulo
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter'
        })

        # Formato de header
        header_format = workbook.add_format({
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1  
        })

        # Formato nímeros
        number_format = workbook.add_format({'num_format': '0.00'}) 

        # Encabezados
        headers = ['Año', 'Calidad Producto', 'Calidad Servicio', 'Disponiblidad', 'Condiciones Pago', 'Precio', 
            'Plazo Entrega', 'Atención Comercial', 'Resolucion Problemas', 'NC', 'SGC', 'Personal Técnico',
            'Total', 'Calificación']  
        
        for col, header in enumerate(headers):
            worksheet.write(1, col, header, header_format)

        worksheet.merge_range('A1:N1', 'HISTÓRICO DE EVALUACIONES', title_format)

        # Datos
        evaluation = self.env['metalesa.supplier.evaluation'].search([('supplier_id', '=', self.id)])
        row = 2
        for record in evaluation:
            worksheet.write(row, 0, record.year)  
            worksheet.write(row, 1, record.calidad_producto, number_format)
            worksheet.write(row, 2, record.calidad_servicio, number_format)
            worksheet.write(row, 3, record.disponiblidad, number_format)
            worksheet.write(row, 4, record.cond_pago, number_format)
            worksheet.write(row, 5, record.precio, number_format)
            worksheet.write(row, 6, record.plazo_entrega, number_format)
            worksheet.write(row, 7, record.atencion_comercial, number_format)
            worksheet.write(row, 8, record.resolucion_problemas, number_format)
            worksheet.write(row, 9, record.nc)
            worksheet.write(row, 10, record.sgc)
            worksheet.write(row, 11, record.personal_tecnico, number_format)
            worksheet.write(row, 12, record.total, number_format)
            worksheet.write(row, 13, record.calificacion)
            row += 1

        # Hoja EVALUACIÓN DE PROVEEDORES (PROCEDIMIENTO ACTUALIZADO 2024)
        worksheet2 = workbook.add_worksheet('Evaluaciones Actualizados')

        # Encabezados
        headers2 = ['Año', 'Calidad Producto/Servicio', 'Precio', 'Plazo Entrega', 
            'Atención Comercial', 'NC', 'SGC', 'Total', 'Calificación']  
        for col, header in enumerate(headers2):
            worksheet2.write(1, col, header, header_format)

        worksheet2.merge_range('A1:I1', 'EVALUACIÓN DE PROVEEDORES (PROCEDIMIENTO ACTUALIZADO DESDE 2024)', title_format)

        # Datos
        evaluation2 = self.env['metalesa.supplier.evaluation.new'].search([('supplier_id', '=', self.id)])
        row = 2
        for record in evaluation2:
            worksheet2.write(row, 0, record.year)  
            worksheet2.write(row, 1, record.product_service_quality, number_format)
            worksheet2.write(row, 2, record.price, number_format)
            worksheet2.write(row, 3, record.delivery_time, number_format)
            worksheet2.write(row, 4, record.nc, number_format)
            worksheet2.write(row, 5, record.sgc, number_format)
            worksheet2.write(row, 6, record.environmental_policy, number_format)
            worksheet2.write(row, 7, record.total, number_format)
            worksheet2.write(row, 8, record.qualification)
            row += 1
      
        workbook.close()
        output.seek(0)

        # Crear el archivo adjunto
        file_data = base64.b64encode(output.read())
        store_fname = 'historico_evaluacion_%s_%s.xlsx' % (self.name, fields.Date.today())
        attachment = self.env['ir.attachment'].create({
            'name': 'historico_evaluacion.xlsx',
            'type': 'binary',
            'datas': file_data,
            'store_fname': store_fname,  # Nombre que se usará en el almacenamiento
            'datas_fname': store_fname,  # Nombre que se usará en la descarga
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        # Descargar el archivo
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true&filename=%s' % (attachment.id, store_fname),
            'target': 'new',
        }

class SupplierEvaluation(models.Model):
    _name = 'metalesa.supplier.evaluation'
    _description = 'Metsalesa Supplier Evaluation'

    @api.model
    def default_get(self, fields):
        res = super(SupplierEvaluation, self).default_get(fields)

        res.update({'year': datetime.today().year})

        return res

    @api.depends('year')
    def _recheck_values(self):
        for record in self:
            """ with this code it never calculates 
            since when finished the state changes and"""
            # if record.state == 'calc':
            #     return

            # if not record.calificacion:
            supplier_id = self.env['res.partner']
            suplier = False
            
            """ 
            When user create new supplier qualification line supplier_id stay in context
            but when this line  is created with save button, context haven't got supplier
            but exist in self
            """
            if record._context.get('supplier'):
                supplier = self._context.get('supplier')
                supplier_id = self.env['res.partner'].browse(supplier)
            
            elif record.supplier_id:
                supplier_id = record.supplier_id

            if supplier_id:
                if record.supplier_id.sgc:
                    record.sgc = 10.0
                else:
                    record.sgc = 5.0

                # Buscar el numero de NC
                year = record.year
                year_start = datetime(year, 1, 1)
                year_end = datetime(year, 12, 31)

                #Get the stage cancel for nonconformities
                cancel_state_id = self.env.ref('mgmtsystem_nonconformity.stage_cancel')

                nc = self.env['mgmtsystem.nonconformity'].search_count([
                    ('partner_id', '=', supplier_id.id),
                    ('create_date', '>=', year_start),
                    ('create_date', '<=', year_end),
                    ('stage_id', '!=', cancel_state_id.id)
                ])

                config_id = self.env['metalesa.supplier.evaluation.config'].search([
                    ('parameter_field', '=', 'nc')
                ])

                if config_id:
                    puntucaion = config_id.search_value_in_range(nc)
                    if not puntucaion:
                        puntucaion = 10
                    record.nc = puntucaion

                if supplier_id.property_supplier_payment_term_id:
                    item = supplier_id.property_supplier_payment_term_id.line_ids.filtered(
                        lambda x: x.value == 'balance'
                    )

                    if item:
                        config_id = self.env['metalesa.supplier.evaluation.config'].search([
                            ('parameter_field', '=', 'cond_pago')
                        ])

                        if config_id:
                            puntucaion = config_id.search_value_in_range(item.days)
                            record.cond_pago = puntucaion
                        else:
                            config_id == 0.0
                else:
                    record.cond_pago = 0.0

    year = fields.Integer(
        string=_("Año"),
        required=True,
    )

    supplier_id = fields.Many2one(
        comodel_name="res.partner",
        string=_('Proveedor')
    )

    tag_ids = fields.Char(
        related='supplier_id.category_id.name'
    )

    calidad_producto = fields.Float(
        string=_('Calidad Producto')
    )

    calidad_servicio = fields.Float(
        string=_('Calidad Servicio')
    )

    disponiblidad = fields.Float(
        string=_('Disponibilidad')
    )

    cond_pago = fields.Float(
        string=_('Cond de pago'),
        compute=_recheck_values,
        store=True,
    )

    precio = fields.Float(
        string=_('Precio')
    )

    plazo_entrega = fields.Float(
        string=_('Plazo Entrega')
    )

    atencion_comercial = fields.Float(
        string=_('Atención C')
    )

    resolucion_problemas = fields.Float(
        string=_('Resolucion Problemas')
    )

    nc = fields.Float(
        string=_('NC'),
        compute=_recheck_values,
        store=True,
    )

    sgc = fields.Float(
        string=_('SGC'),
        compute=_recheck_values,
        store=True,
    )

    personal_tecnico = fields.Float(
        string=_('Personal Tecnico')
    )

    total = fields.Float(
        string=_('Total'),
        readonly=True,
    )

    calificacion = fields.Char(
        string=_('Calificación'),
        readonly=True,
    )

    state = fields.Selection(
        selection=[('calc', 'Calculado')],
    )

    @api.multi
    def calcular_valores_staticos(self):
        ConfigObj = self.env['metalesa.supplier.evaluation.config']

        lista_parcial = []
        lista_pesos = []
        for record in self:
            record._recheck_values()

            # Calidad Producto
            conf_id = ConfigObj.search([
                ('parameter_field', '=', 'calidad_producto')
            ])

            lista_parcial.append(record.calidad_producto * conf_id.peso)
            lista_pesos.append(conf_id.peso)

            # Calidad Servicio
            conf_id = ConfigObj.search([
                ('parameter_field', '=', 'calidad_servicio')
            ])

            lista_parcial.append(record.calidad_servicio * conf_id.peso)
            lista_pesos.append(conf_id.peso)

            # Disponibilidad
            conf_id = ConfigObj.search([
                ('parameter_field', '=', 'disponiblidad')
            ])

            lista_parcial.append(record.disponiblidad * conf_id.peso)
            lista_pesos.append(conf_id.peso)

            # Cond Pago
            conf_id = ConfigObj.search([
                ('parameter_field', '=', 'cond_pago')
            ])

            lista_parcial.append(record.cond_pago * conf_id.peso)
            lista_pesos.append(conf_id.peso)

            # Precio
            conf_id = ConfigObj.search([
                ('parameter_field', '=', 'precio')
            ])

            lista_parcial.append(record.precio * conf_id.peso)
            lista_pesos.append(conf_id.peso)

            # Plazo entrega
            conf_id = ConfigObj.search([
                ('parameter_field', '=', 'plazo_entrega')
            ])

            lista_parcial.append(record.plazo_entrega * conf_id.peso)
            lista_pesos.append(conf_id.peso)

            # Att comercial
            conf_id = ConfigObj.search([
                ('parameter_field', '=', 'atencion_comercial')
            ])

            lista_parcial.append(record.atencion_comercial * conf_id.peso)
            lista_pesos.append(conf_id.peso)

            # Res problemas
            conf_id = ConfigObj.search([
                ('parameter_field', '=', 'resolucion_problemas')
            ])

            lista_parcial.append(record.resolucion_problemas * conf_id.peso)
            lista_pesos.append(conf_id.peso)

            # NC
            conf_id = ConfigObj.search([
                ('parameter_field', '=', 'nc')
            ])

            lista_parcial.append(record.nc * conf_id.peso)
            lista_pesos.append(conf_id.peso)

            # SGC
            conf_id = ConfigObj.search([
                ('parameter_field', '=', 'sgc')
            ])

            lista_parcial.append(record.sgc * conf_id.peso)
            lista_pesos.append(conf_id.peso)

            # Personal Tecnico
            conf_id = ConfigObj.search([
                ('parameter_field', '=', 'personal_tecnico')
            ])

            lista_parcial.append(record.personal_tecnico * conf_id.peso)
            lista_pesos.append(conf_id.peso)

            if not sum(lista_pesos):
                val = sum(lista_parcial)
            else:
                val = sum(lista_parcial) / sum(lista_pesos)

            record.total = val

            conf_id = ConfigObj.search([
                ('parameter_field', '=', 'calificacion')
            ])

            puntucaion = conf_id.search_value_in_range_txt(val)

            record.calificacion = puntucaion

            record.state = 'calc'

class SupplierEvaluationConfig(models.Model):
    _name = 'metalesa.supplier.evaluation.config'
    _rec_name = 'parameter_field'
    _description = 'Configuration Metalesa Supplier Evaluation'

    @api.constrains('parameter_field')
    def parameter_field_unique(self):
        records = self.env['metalesa.supplier.evaluation.config'].search([
            ('parameter_field', '=', self.parameter_field)
        ])

        if len(records) > 1:
            raise exceptions.ValidationError(
                _("No puede tener dos configuraciones del mismo campo")
            )

    def field_form_model(self):
        fields = self.env['metalesa.supplier.evaluation'].fields_get()

        fields.pop('create_date', None)
        fields.pop('create_uid', None)
        fields.pop('write_uid', None)
        fields.pop('write_date', None)
        fields.pop('supplier_id', None)
        fields.pop('__last_update', None)
        fields.pop('display_name', None)

        return [(k, v['string']) for k, v in fields.items()]

    parameter_field = fields.Selection(
        selection=field_form_model,
        string=_('Descripcion Parametro'),
        required=True,
    )

    peso = fields.Float(
        string=_('Peso')
    )

    user_logic = fields.Selection(
        selection=[
            ('user', _('Usuario')),
            ('logic', _('Lógica'))
        ],
        string=_('Lógica Cálculo'),
        required=True,
    )

    config_range = fields.Selection(
        selection=[
            ('s', _('Sí')),
            ('n', _('No'))
        ],
        string=_('Rango Configurable'),
    )

    config_logic_ids = fields.One2many(
        comodel_name='metalesa.supplier.evaluation.config.range',
        inverse_name='config_logic_id'
    )

    tipo_puntuacion = fields.Selection(
        selection=[
            ('number', _('Numerica')),
            ('text', _('Texto'))
        ],
        string=_('Tipo Puntucacion'),
    )

    @api.multi
    def search_value_in_range(self, value):
        if self.config_logic_ids:
            result = self.config_logic_ids.filtered(
                lambda x: value >= x.range_min and value <= x.range_max
            )

            return result.puntuacion if result else False
        else:
            return False

    @api.multi
    def search_value_in_range_txt(self, value):
        if self.config_logic_ids:
            result = self.config_logic_ids.filtered(
                lambda x: value >= x.range_min and value <= x.range_max
            )

            return result.puntuacion_str if result else False
        else:
            return False


class SupplierEvaluationConfigRange(models.Model):
    _name = 'metalesa.supplier.evaluation.config.range'
    _description = 'Configuration Metalesa Supplier Evaluation Range'

    config_logic_id = fields.Many2one(
        comodel_name='metalesa.supplier.evaluation.config'
    )

    parameter_field = fields.Selection(
        related="config_logic_id.parameter_field"
    )

    range_min = fields.Float(
        string=_("Desde")
    )

    range_max = fields.Float(
        string=_("Hasta")
    )

    puntuacion = fields.Float(
        string=_("Puntuación Numerica")
    )

    puntuacion_str = fields.Char(
        string=_("Puntuación Textual")
    )

class SupplierEvaluationNew(models.Model):
    _name = 'metalesa.supplier.evaluation.new'
    _description = 'Metsalesa Supplier Evaluation New'

    @api.model
    def default_get(self, fields):
        res = super(SupplierEvaluationNew, self).default_get(fields)
        res.update({'year': datetime.today().year})
        return res

    @api.depends('year')
    def _recheck_values(self):
        for record in self:
            """ 
            When user create new supplier qualification line supplier_id stay in context
            but when this line  is created with save button, context haven't got supplier
            but exist in self
            """
            if record._context.get('supplier'):
                supplier = self._context.get('supplier')
                partner_id = self.env['res.partner'].browse(supplier)
            
            elif record.supplier_id:
                partner_id = record.supplier_id

            if partner_id:
                if record.supplier_id.sgc:
                    record.sgc = 10.0
                else:
                    record.sgc = 5.0

                # Buscar el numero de NC
                year = record.year
                year_start = datetime(year, 1, 1)
                year_end = datetime(year, 12, 31)

                #Get the stage cancel for nonconformities
                cancel_state_id = self.env.ref('mgmtsystem_nonconformity.stage_cancel')

                nc = self.env['mgmtsystem.nonconformity'].search_count([
                    ('partner_id', '=', partner_id.id),
                    ('create_date', '>=', year_start),
                    ('create_date', '<=', year_end),
                    ('stage_id', '!=', cancel_state_id.id)
                ])

                config_id = self.env['metalesa.supplier.evaluation.config'].search([
                    ('parameter_field', '=', 'nc')
                ])

                if config_id:
                    puntucaion = config_id.search_value_in_range(nc)
                    if not puntucaion:
                        puntucaion = 10
                    record.nc = puntucaion

    year = fields.Integer(
        string=_("Año"),
        required=True,
    )
    product_service_quality = fields.Float(
        string=_('Calidad Producto/Servicio')
    )
    price = fields.Float(
        string=_('Precio')
    )
    delivery_time = fields.Float(
        string=_('Plazo Entrega')
    )
    commercial_attention = fields.Float(
        string=_('Atención Comercial')
    )
    nc = fields.Float(
        string=_('NC'),
        compute=_recheck_values,
        store=True,
    )
    sgc = fields.Float(
        string=_('SGC'),
        compute=_recheck_values,
        store=True,
    )
    environmental_policy = fields.Float(
        string=_('Politica Medioambiente'),
    )
    total = fields.Float(
        string=_('Total'),
        readonly=True,
    )
    qualification = fields.Char(
        string=_('Calificación'),
        readonly=True,
    )
    supplier_id = fields.Many2one(
        comodel_name="res.partner",
        string=_('Proveedor')
    )


    @api.multi
    def calcular_valores_staticos(self):
        ConfigObj = self.env['metalesa.supplier.evaluation.config.new']

        lista_parcial = []
        lista_pesos = []
        for record in self:
            record._recheck_values()

            # Calidad Producto/Servicio
            conf_id = ConfigObj.search([
                ('parameter_field', '=', 'product_service_quality')
            ])

            lista_parcial.append(record.product_service_quality * conf_id.peso)
            lista_pesos.append(conf_id.peso)

            # Precio
            conf_id = ConfigObj.search([
                ('parameter_field', '=', 'price')
            ])

            lista_parcial.append(record.price * conf_id.peso)
            lista_pesos.append(conf_id.peso)

            # Plazo entrega
            conf_id = ConfigObj.search([
                ('parameter_field', '=', 'delivery_time')
            ])

            lista_parcial.append(record.delivery_time * conf_id.peso)
            lista_pesos.append(conf_id.peso)

            # Att comercial
            conf_id = ConfigObj.search([
                ('parameter_field', '=', 'commercial_attention')
            ])

            lista_parcial.append(record.commercial_attention * conf_id.peso)
            lista_pesos.append(conf_id.peso)

            # Politica Medioambiental
            conf_id = ConfigObj.search([
                ('parameter_field', '=', 'environmental_policy')
            ])

            lista_parcial.append(record.environmental_policy * conf_id.peso)
            lista_pesos.append(conf_id.peso)

            # NC
            conf_id = ConfigObj.search([
                ('parameter_field', '=', 'nc')
            ])

            lista_parcial.append(record.nc * conf_id.peso)
            lista_pesos.append(conf_id.peso)

            # SGC
            conf_id = ConfigObj.search([
                ('parameter_field', '=', 'sgc')
            ])

            lista_parcial.append(record.sgc * conf_id.peso)
            lista_pesos.append(conf_id.peso)

            if not sum(lista_pesos):
                val = sum(lista_parcial)
            else:
                val = sum(lista_parcial) / sum(lista_pesos)

            record.total = val

            conf_id = ConfigObj.search([
                ('parameter_field', '=', 'qualification')
            ])

            puntucaion = conf_id.search_value_in_range_txt(val)

            record.qualification = puntucaion

            # record.state = 'calc'

    @api.multi
    def search_value_in_range_txt(self, value):
        if self.config_logic_ids:
            result = self.config_logic_ids.filtered(
                lambda x: value >= x.range_min and value <= x.range_max
            )

            return result.puntuacion_str if result else False
        else:
            return False
        
class SupplierEvaluationConfigNew(models.Model):
    _name = 'metalesa.supplier.evaluation.config.new'
    _rec_name = 'parameter_field'
    _description = 'Configuration Metalesa Supplier Evaluation Nuevo'

    @api.constrains('parameter_field')
    def parameter_field_unique(self):
        records = self.env['metalesa.supplier.evaluation.config.new'].search([
            ('parameter_field', '=', self.parameter_field)
        ])

        if len(records) > 1:
            raise exceptions.ValidationError(
                _("No puede tener dos configuraciones del mismo campo")
            )

    def field_form_model(self):
        fields = self.env['metalesa.supplier.evaluation.new'].fields_get()

        fields.pop('create_date', None)
        fields.pop('create_uid', None)
        fields.pop('write_uid', None)
        fields.pop('write_date', None)
        fields.pop('supplier_id', None)
        fields.pop('__last_update', None)
        fields.pop('display_name', None)

        return [(k, v['string']) for k, v in fields.items()]

    parameter_field = fields.Selection(
        selection=field_form_model,
        string=_('Descripcion Parametro'),
        required=True,
    )

    peso = fields.Float(
        string=_('Peso')
    )

    user_logic = fields.Selection(
        selection=[
            ('user', _('Usuario')),
            ('logic', _('Lógica'))
        ],
        string=_('Lógica Cálculo'),
        required=True,
    )

    config_range = fields.Selection(
        selection=[
            ('s', _('Sí')),
            ('n', _('No'))
        ],
        string=_('Rango Configurable'),
    )

    config_logic_ids = fields.One2many(
        comodel_name='metalesa.supplier.evaluation.config.range.new',
        inverse_name='config_logic_id'
    )

    tipo_puntuacion = fields.Selection(
        selection=[
            ('number', _('Numerica')),
            ('text', _('Texto'))
        ],
        string=_('Tipo Puntucacion'),
    )

    @api.multi
    def search_value_in_range(self, value):
        if self.config_logic_ids:
            result = self.config_logic_ids.filtered(
                lambda x: value >= x.range_min and value <= x.range_max
            )

            return result.puntuacion if result else False
        else:
            return False

    @api.multi
    def search_value_in_range_txt(self, value):
        if self.config_logic_ids:
            result = self.config_logic_ids.filtered(
                lambda x: value >= x.range_min and value <= x.range_max
            )

            return result.puntuacion_str if result else False
        else:
            return False
        
class SupplierEvaluationConfigRangeNew(models.Model):
    _name = 'metalesa.supplier.evaluation.config.range.new'
    _description = 'Configuration Metalesa Supplier Evaluation Range New'

    config_logic_id = fields.Many2one(
        comodel_name='metalesa.supplier.evaluation.config.new'
    )

    parameter_field = fields.Selection(
        related="config_logic_id.parameter_field"
    )

    range_min = fields.Float(
        string=_("Desde")
    )

    range_max = fields.Float(
        string=_("Hasta")
    )

    puntuacion = fields.Float(
        string=_("Puntuación Numérica")
    )

    puntuacion_str = fields.Char(
        string=_("Puntuación Textual")
    )
    