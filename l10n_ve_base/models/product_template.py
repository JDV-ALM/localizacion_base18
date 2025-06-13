# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Venezuelan product classifications
    seniat_code = fields.Char(
        string='Código SENIAT',
        help='Código del producto según clasificación SENIAT'
    )
    
    aranceles_code = fields.Char(
        string='Código Arancelario',
        help='Código arancelario para productos importados'
    )
    
    # Venezuelan tax settings
    tax_exempt_reason = fields.Selection([
        ('basic_need', 'Producto de Primera Necesidad'),
        ('medicine', 'Medicamento'),
        ('education', 'Material Educativo'),
        ('export', 'Producto de Exportación'),
        ('agricultural', 'Producto Agrícola'),
        ('other', 'Otra Exención'),
    ], string='Motivo de Exención')
    
    # Price controls (Venezuela specific)
    is_price_regulated = fields.Boolean(
        string='Precio Regulado',
        help='Producto con precio regulado por el Estado'
    )
    regulated_price = fields.Float(
        string='Precio Regulado',
        help='Precio máximo establecido por regulación'
    )
    regulation_date = fields.Date(
        string='Fecha de Regulación',
        help='Fecha de entrada en vigencia de la regulación de precio'
    )
    
    # Venezuelan currency pricing
    price_usd = fields.Float(
        string='Precio en USD',
        digits='Product Price',
        help='Precio de referencia en dólares estadounidenses'
    )
    price_eur = fields.Float(
        string='Precio en EUR',
        digits='Product Price',
        help='Precio de referencia en euros'
    )
    
    # Import/Export information
    is_imported = fields.Boolean(
        string='Producto Importado',
        help='Indica si el producto es importado'
    )
    country_of_origin = fields.Many2one(
        'res.country',
        string='País de Origen',
        help='País de origen del producto'
    )
    import_permit_required = fields.Boolean(
        string='Requiere Permiso de Importación',
        help='Indica si requiere permisos especiales para importación'
    )
    
    # Venezuelan product categories
    product_category_ve = fields.Selection([
        ('food', 'Alimentos'),
        ('medicine', 'Medicinas'),
        ('clothing', 'Vestimenta'),
        ('electronics', 'Electrónicos'),
        ('automotive', 'Automotriz'),
        ('construction', 'Construcción'),
        ('industrial', 'Industrial'),
        ('agricultural', 'Agrícola'),
        ('services', 'Servicios'),
        ('other', 'Otros'),
    ], string='Categoría Venezolana')
    
    # Price calculation based on currency
    @api.depends('price_usd', 'price_eur')
    def _compute_list_price_from_foreign(self):
        """Compute list price from foreign currency prices"""
        for product in self:
            if product.price_usd:
                usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
                if usd_currency:
                    rate = usd_currency._get_conversion_rate(
                        usd_currency,
                        self.env.company.currency_id,
                        self.env.company,
                        fields.Date.today()
                    )
                    product.list_price = product.price_usd * rate
    
    @api.onchange('product_category_ve')
    def _onchange_product_category_ve(self):
        """Set default tax configuration based on Venezuelan category"""
        if self.product_category_ve == 'food':
            # Food products might have different tax rates
            self.tax_exempt_reason = 'basic_need'
        elif self.product_category_ve == 'medicine':
            self.tax_exempt_reason = 'medicine'
        elif self.product_category_ve == 'services':
            # Services typically have different tax treatment
            pass
    
    @api.onchange('is_price_regulated')
    def _onchange_is_price_regulated(self):
        """Set regulation date when price is regulated"""
        if self.is_price_regulated and not self.regulation_date:
            self.regulation_date = fields.Date.today()
    
    @api.constrains('regulated_price', 'list_price')
    def _check_regulated_price(self):
        """Ensure selling price doesn't exceed regulated price"""
        for product in self:
            if (product.is_price_regulated and 
                product.regulated_price and 
                product.list_price > product.regulated_price):
                raise ValidationError(_(
                    'El precio de venta no puede exceder el precio regulado de %s'
                ) % product.regulated_price)
    
    def get_venezuelan_product_info(self):
        """Get Venezuelan product information for reports"""
        self.ensure_one()
        return {
            'name': self.name,
            'seniat_code': self.seniat_code or '',
            'aranceles_code': self.aranceles_code or '',
            'category_ve': self.product_category_ve or '',
            'tax_exempt_reason': self.tax_exempt_reason or '',
            'is_price_regulated': self.is_price_regulated,
            'regulated_price': self.regulated_price if self.is_price_regulated else 0,
            'is_imported': self.is_imported,
            'country_of_origin': self.country_of_origin.name if self.country_of_origin else '',
            'price_usd': self.price_usd,
            'price_eur': self.price_eur,
        }


class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    # Lot/Serial specific information for Venezuela
    import_batch = fields.Char(
        string='Lote de Importación',
        help='Número de lote de importación'
    )
    import_date = fields.Date(
        string='Fecha de Importación',
        help='Fecha de importación del lote'
    )
    
    def get_current_price_bolivars(self):
        """Get current price in Venezuelan bolívars"""
        self.ensure_one()
        ves_currency = self.env['res.currency'].search([('name', '=', 'VES')], limit=1)
        if ves_currency and self.env.company.currency_id != ves_currency:
            return self.list_price * ves_currency._get_conversion_rate(
                self.env.company.currency_id,
                ves_currency,
                self.env.company,
                fields.Date.today()
            )
        return self.list_price
    
    def get_current_price_usd(self):
        """Get current price in USD"""
        self.ensure_one()
        if self.price_usd:
            return self.price_usd
        
        usd_currency = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        if usd_currency and self.env.company.currency_id != usd_currency:
            return self.list_price / usd_currency._get_conversion_rate(
                usd_currency,
                self.env.company.currency_id,
                self.env.company,
                fields.Date.today()
            )
        return self.list_price