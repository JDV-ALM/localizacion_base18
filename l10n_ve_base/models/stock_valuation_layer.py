# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    # Venezuelan valuation fields
    value_usd = fields.Float(
        string='Valor en USD',
        digits='Product Price',
        help='Valor de la capa de valuación en dólares estadounidenses'
    )
    
    value_eur = fields.Float(
        string='Valor en EUR',
        digits='Product Price',
        help='Valor de la capa de valuación en euros'
    )
    
    # Exchange rate used for valuation
    exchange_rate_ves_usd = fields.Float(
        string='Tasa VES/USD',
        digits=(12, 6),
        help='Tasa de cambio VES/USD utilizada en la valuación'
    )
    
    exchange_rate_ves_eur = fields.Float(
        string='Tasa VES/EUR',
        digits=(12, 6),
        help='Tasa de cambio VES/EUR utilizada en la valuación'
    )
    
    # Venezuelan specific valuation method
    valuation_method_ve = fields.Selection([
        ('fifo', 'PEPS (Primero en Entrar, Primero en Salir)'),
        ('lifo', 'UEPS (Último en Entrar, Primero en Salir)'),
        ('average', 'Promedio Ponderado'),
        ('standard', 'Costo Estándar'),
    ], string='Método de Valuación Venezolano',
        related='product_id.categ_id.property_cost_method',
        readonly=True)
    
    # Import cost tracking
    import_cost = fields.Float(
        string='Costo de Importación',
        digits='Product Price',
        help='Costo de importación del producto'
    )
    
    import_currency_id = fields.Many2one(
        'res.currency',
        string='Moneda de Importación',
        help='Moneda utilizada en la importación'
    )
    
    # Venezuelan accounting period
    accounting_period = fields.Char(
        string='Período Contable',
        compute='_compute_accounting_period',
        store=True,
        help='Período contable venezolano (MM/YYYY)'
    )
    
    @api.depends('create_date')
    def _compute_accounting_period(self):
        """Compute Venezuelan accounting period"""
        for layer in self:
            if layer.create_date:
                layer.accounting_period = layer.create_date.strftime('%m/%Y')
            else:
                layer.accounting_period = ''
    
    @api.model
    def create(self, vals):
        """Override create to compute foreign currency values"""
        layer = super().create(vals)
        layer._compute_foreign_currency_values()
        return layer
    
    def write(self, vals):
        """Override write to recompute foreign currency values if needed"""
        result = super().write(vals)
        if 'value' in vals or 'unit_cost' in vals:
            self._compute_foreign_currency_values()
        return result
    
    def _compute_foreign_currency_values(self):
        """Compute values in foreign currencies"""
        for layer in self:
            # Get USD conversion
            usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
            if usd_currency:
                rate_usd = self.env.company.currency_id._get_conversion_rate(
                    self.env.company.currency_id,
                    usd_currency,
                    self.env.company,
                    layer.create_date.date() if layer.create_date else fields.Date.today()
                )
                layer.value_usd = layer.value * rate_usd if rate_usd else 0
                layer.exchange_rate_ves_usd = 1 / rate_usd if rate_usd else 0
            
            # Get EUR conversion
            eur_currency = self.env['res.currency'].search([('name', '=', 'EUR')], limit=1)
            if eur_currency:
                rate_eur = self.env.company.currency_id._get_conversion_rate(
                    self.env.company.currency_id,
                    eur_currency,
                    self.env.company,
                    layer.create_date.date() if layer.create_date else fields.Date.today()
                )
                layer.value_eur = layer.value * rate_eur if rate_eur else 0
                layer.exchange_rate_ves_eur = 1 / rate_eur if rate_eur else 0
    
    def get_venezuelan_valuation_info(self):
        """Get Venezuelan valuation information"""
        self.ensure_one()
        return {
            'product_name': self.product_id.name,
            'quantity': self.quantity,
            'unit_cost': self.unit_cost,
            'value_ves': self.value,
            'value_usd': self.value_usd,
            'value_eur': self.value_eur,
            'exchange_rate_usd': self.exchange_rate_ves_usd,
            'exchange_rate_eur': self.exchange_rate_ves_eur,
            'valuation_method': self.valuation_method_ve,
            'accounting_period': self.accounting_period,
            'import_cost': self.import_cost,
            'import_currency': self.import_currency_id.name if self.import_currency_id else '',
        }


class StockMove(models.Model):
    _inherit = 'stock.move'
    
    # Venezuelan stock move fields
    import_reference = fields.Char(
        string='Referencia de Importación',
        help='Referencia del documento de importación'
    )
    
    customs_value = fields.Float(
        string='Valor Aduanero',
        digits='Product Price',
        help='Valor declarado en aduana'
    )
    
    def _create_in_svl(self, forced_quantity=None):
        """Override to set Venezuelan specific values"""
        svl = super()._create_in_svl(forced_quantity)
        
        # Set import information if available
        if self.purchase_line_id and self.purchase_line_id.order_id.is_import_purchase:
            for layer in svl:
                if self.purchase_line_id.import_unit_cost:
                    layer.import_cost = self.purchase_line_id.import_unit_cost * layer.quantity
                if self.purchase_line_id.import_currency_id:
                    layer.import_currency_id = self.purchase_line_id.import_currency_id.id
        
        return svl


class ProductCategory(models.Model):
    _inherit = 'product.category'
    
    # Venezuelan category settings
    seniat_category_code = fields.Char(
        string='Código Categoría SENIAT',
        help='Código de categoría según SENIAT'
    )
    
    # Valuation method description in Spanish
    property_cost_method_description = fields.Char(
        string='Descripción Método Costos',
        compute='_compute_cost_method_description',
        help='Descripción del método de costos en español'
    )
    
    @api.depends('property_cost_method')
    def _compute_cost_method_description(self):
        """Compute cost method description in Spanish"""
        descriptions = {
            'fifo': 'PEPS (Primero en Entrar, Primero en Salir)',
            'lifo': 'UEPS (Último en Entrar, Primero en Salir)', 
            'average': 'Promedio Ponderado',
            'standard': 'Costo Estándar',
        }
        
        for category in self:
            category.property_cost_method_description = descriptions.get(
                category.property_cost_method, 
                category.property_cost_method or ''
            )