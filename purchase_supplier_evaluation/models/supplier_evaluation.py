# -*- coding: utf-8 -*-

from odoo import fields, models, api, exceptions, _

from datetime import datetime, date


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sgc = fields.Boolean(
        string=_("SGC"),
    )

    calificacion_proveedor_ids = fields.One2many(
        comodel_name='metalesa.supplier.evaluation',
        inverse_name='supplier_id',
    )


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
