# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountTax(models.Model):
    _inherit = 'account.tax'

    # Venezuelan tax types
    tax_type_ve = fields.Selection([
        ('vat', 'IVA - Impuesto al Valor Agregado'),
        ('islr', 'ISLR - Impuesto Sobre la Renta'),
        ('municipal', 'Impuesto Municipal'),
        ('igtf', 'IGTF - Impuesto a las Grandes Transacciones Financieras'),
        ('other', 'Otro Impuesto'),
    ], string='Tipo de Impuesto Venezolano', default='other')
    
    # Withholding tax configuration
    is_withholding = fields.Boolean(
        string='Es Retención',
        help='Indica si este impuesto es una retención'
    )
    withholding_type = fields.Selection([
        ('wh_vat', 'Retención de IVA'),
        ('wh_islr', 'Retención de ISLR'),
        ('wh_municipal', 'Retención Municipal'),
    ], string='Tipo de Retención')
    
    # Venezuelan tax codes for SENIAT
    seniat_code = fields.Char(
        string='Código SENIAT',
        help='Código del impuesto según SENIAT'
    )
    
    # Minimum amount for tax application
    minimum_amount = fields.Float(
        string='Monto Mínimo',
        help='Monto mínimo para aplicar el impuesto'
    )
    
    # Rate for withholding calculation
    withholding_rate = fields.Float(
        string='Tasa de Retención (%)',
        help='Porcentaje de retención aplicable'
    )
    
    # Configuration for IGTF
    is_igtf = fields.Boolean(
        string='Es IGTF',
        help='Indica si este impuesto es IGTF'
    )
    
    # Exempt conditions
    exempt_national = fields.Boolean(
        string='Exento Nacional',
        help='Producto exento a nivel nacional'
    )
    exempt_state = fields.Boolean(
        string='Exento Estadal',
        help='Producto exento a nivel estadal'
    )
    exempt_municipal = fields.Boolean(
        string='Exento Municipal',
        help='Producto exento a nivel municipal'
    )
    
    @api.constrains('tax_type_ve', 'amount')
    def _check_venezuelan_tax_rates(self):
        """Validate Venezuelan tax rates"""
        for tax in self:
            if tax.tax_type_ve == 'vat':
                # Common VAT rates in Venezuela: 0%, 16%
                if tax.amount not in [0, 16]:
                    raise ValidationError(_(
                        'Las tasas de IVA válidas en Venezuela son 0% y 16%'
                    ))
            elif tax.tax_type_ve == 'igtf':
                # IGTF rate is typically 3%
                if tax.amount != 3:
                    raise ValidationError(_(
                        'La tasa de IGTF en Venezuela es 3%'
                    ))
    
    @api.onchange('tax_type_ve')
    def _onchange_tax_type_ve(self):
        """Set default values based on Venezuelan tax type"""
        if self.tax_type_ve == 'vat':
            self.name = 'IVA 16%'
            self.amount = 16
            self.seniat_code = 'IVA16'
        elif self.tax_type_ve == 'islr':
            self.name = 'ISLR'
            self.amount = 3
            self.is_withholding = True
            self.withholding_type = 'wh_islr'
            self.withholding_rate = 100
            self.seniat_code = 'ISLR'
        elif self.tax_type_ve == 'municipal':
            self.name = 'Retención Municipal'
            self.amount = 1
            self.is_withholding = True
            self.withholding_type = 'wh_municipal'
            self.withholding_rate = 100
        elif self.tax_type_ve == 'igtf':
            self.name = 'IGTF 3%'
            self.amount = 3
            self.is_igtf = True
            self.seniat_code = 'IGTF'
    
    @api.onchange('is_withholding')
    def _onchange_is_withholding(self):
        """Configure withholding tax settings"""
        if self.is_withholding:
            self.type_tax_use = 'purchase'
            self.amount_type = 'percent'
            if not self.withholding_rate:
                self.withholding_rate = 100
    
    def compute_all(self, price_unit, currency=None, quantity=1.0, product=None, partner=None, is_refund=False, handle_price_include=True, include_caba_tags=False, fixed_multiplicator=1):
        """Override to handle Venezuelan tax computations"""
        # Check minimum amount for tax application
        if self.minimum_amount and price_unit * quantity < self.minimum_amount:
            # Return zero tax if below minimum
            return {
                'taxes': [],
                'total_excluded': price_unit * quantity,
                'total_included': price_unit * quantity,
                'base_tags': [],
                'tax_tags': [],
            }
        
        # Standard tax computation
        result = super().compute_all(
            price_unit, currency, quantity, product, partner, 
            is_refund, handle_price_include, include_caba_tags, fixed_multiplicator
        )
        
        # Apply withholding calculation if applicable
        if self.is_withholding and self.withholding_rate != 100:
            for tax_result in result['taxes']:
                if tax_result['id'] == self.id:
                    tax_result['amount'] = tax_result['amount'] * (self.withholding_rate / 100)
        
        return result
    
    def get_venezuelan_tax_info(self):
        """Get Venezuelan tax information for reports"""
        self.ensure_one()
        return {
            'name': self.name,
            'type': self.tax_type_ve,
            'rate': self.amount,
            'seniat_code': self.seniat_code or '',
            'is_withholding': self.is_withholding,
            'withholding_type': self.withholding_type or '',
            'minimum_amount': self.minimum_amount,
        }
    
    @api.model
    def create_venezuelan_default_taxes(self, company):
        """Create default Venezuelan taxes for a company"""
        taxes_data = [
            {
                'name': 'IVA Exento',
                'amount': 0,
                'type_tax_use': 'sale',
                'tax_type_ve': 'vat',
                'seniat_code': 'IVA0',
                'company_id': company.id,
            },
            {
                'name': 'IVA 16%',
                'amount': 16,
                'type_tax_use': 'sale',
                'tax_type_ve': 'vat',
                'seniat_code': 'IVA16',
                'company_id': company.id,
            },
            {
                'name': 'Retención IVA 75%',
                'amount': -12,  # 75% of 16%
                'type_tax_use': 'purchase',
                'tax_type_ve': 'vat',
                'is_withholding': True,
                'withholding_type': 'wh_vat',
                'withholding_rate': 75,
                'seniat_code': 'RETIVA75',
                'company_id': company.id,
            },
            {
                'name': 'Retención ISLR 3%',
                'amount': -3,
                'type_tax_use': 'purchase',
                'tax_type_ve': 'islr',
                'is_withholding': True,
                'withholding_type': 'wh_islr',
                'withholding_rate': 100,
                'seniat_code': 'ISLR3',
                'minimum_amount': 3000,
                'company_id': company.id,
            },
            {
                'name': 'Retención Municipal 1%',
                'amount': -1,
                'type_tax_use': 'purchase',
                'tax_type_ve': 'municipal',
                'is_withholding': True,
                'withholding_type': 'wh_municipal',
                'withholding_rate': 100,
                'minimum_amount': 1000,
                'company_id': company.id,
            },
            {
                'name': 'IGTF 3%',
                'amount': 3,
                'type_tax_use': 'none',
                'tax_type_ve': 'igtf',
                'is_igtf': True,
                'seniat_code': 'IGTF3',
                'company_id': company.id,
            },
        ]
        
        created_taxes = []
        for tax_data in taxes_data:
            existing_tax = self.search([
                ('name', '=', tax_data['name']),
                ('company_id', '=', company.id)
            ], limit=1)
            if not existing_tax:
                tax = self.create(tax_data)
                created_taxes.append(tax)
        
        return created_taxes