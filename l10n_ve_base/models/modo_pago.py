# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ModoPago(models.Model):
    _name = 'modo.pago'
    _description = 'Modo de Pago Venezolano'
    _order = 'sequence, name'

    name = fields.Char(
        string='Nombre',
        required=True,
        help='Nombre del modo de pago'
    )
    
    code = fields.Char(
        string='Código',
        required=True,
        help='Código único del modo de pago'
    )
    
    sequence = fields.Integer(
        string='Secuencia',
        default=10,
        help='Orden de presentación'
    )
    
    active = fields.Boolean(
        string='Activo',
        default=True
    )
    
    description = fields.Text(
        string='Descripción',
        help='Descripción detallada del modo de pago'
    )
    
    # Venezuelan payment method types
    payment_type = fields.Selection([
        ('cash', 'Efectivo'),
        ('check', 'Cheque'),
        ('transfer', 'Transferencia'),
        ('card', 'Tarjeta'),
        ('electronic', 'Pago Electrónico'),
        ('mobile', 'Pago Móvil'),
        ('other', 'Otro'),
    ], string='Tipo de Pago', required=True, default='cash')
    
    # IGTF application
    applies_igtf = fields.Boolean(
        string='Aplica IGTF',
        help='Este modo de pago está sujeto a IGTF'
    )
    
    igtf_rate = fields.Float(
        string='Tasa IGTF (%)',
        default=3.0,
        help='Porcentaje de IGTF aplicable'
    )
    
    # Bank specific fields
    requires_bank = fields.Boolean(
        string='Requiere Banco',
        help='Este modo de pago requiere especificar un banco'
    )
    
    bank_id = fields.Many2one(
        'res.bank',
        string='Banco',
        help='Banco asociado al modo de pago'
    )
    
    # Journal configuration
    journal_id = fields.Many2one(
        'account.journal',
        string='Diario Contable',
        help='Diario contable asociado al modo de pago'
    )
    
    # Currency settings
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        help='Moneda asociada al modo de pago'
    )
    
    # Account settings
    account_id = fields.Many2one(
        'account.account',
        string='Cuenta Contable',
        help='Cuenta contable para este modo de pago'
    )
    
    # Venezuelan specific settings
    seniat_code = fields.Char(
        string='Código SENIAT',
        help='Código del modo de pago según SENIAT'
    )
    
    is_foreign_currency = fields.Boolean(
        string='Moneda Extranjera',
        help='Este modo de pago maneja moneda extranjera'
    )
    
    # Company
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        default=lambda self: self.env.company
    )
    
    @api.onchange('payment_type')
    def _onchange_payment_type(self):
        """Set default values based on payment type"""
        if self.payment_type in ['transfer', 'card', 'electronic', 'mobile']:
            self.applies_igtf = True
            self.requires_bank = True
        elif self.payment_type == 'cash':
            self.applies_igtf = False
            self.requires_bank = False
        elif self.payment_type == 'check':
            self.applies_igtf = False
            self.requires_bank = True
    
    @api.onchange('applies_igtf')
    def _onchange_applies_igtf(self):
        """Set IGTF rate when enabled"""
        if self.applies_igtf and not self.igtf_rate:
            self.igtf_rate = 3.0
    
    @api.model
    def create_venezuelan_default_payment_methods(self, company):
        """Create default Venezuelan payment methods"""
        methods_data = [
            {
                'name': 'Efectivo',
                'code': 'EFE',
                'payment_type': 'cash',
                'applies_igtf': False,
                'seniat_code': '01',
                'sequence': 1,
            },
            {
                'name': 'Cheque',
                'code': 'CHE',
                'payment_type': 'check',
                'applies_igtf': False,
                'requires_bank': True,
                'seniat_code': '02',
                'sequence': 2,
            },
            {
                'name': 'Transferencia Bancaria',
                'code': 'TRA',
                'payment_type': 'transfer',
                'applies_igtf': True,
                'requires_bank': True,
                'seniat_code': '03',
                'sequence': 3,
            },
            {
                'name': 'Tarjeta de Débito',
                'code': 'TDD',
                'payment_type': 'card',
                'applies_igtf': True,
                'requires_bank': True,
                'seniat_code': '04',
                'sequence': 4,
            },
            {
                'name': 'Tarjeta de Crédito',
                'code': 'TDC',
                'payment_type': 'card',
                'applies_igtf': True,
                'requires_bank': True,
                'seniat_code': '05',
                'sequence': 5,
            },
            {
                'name': 'Pago Móvil',
                'code': 'PMO',
                'payment_type': 'mobile',
                'applies_igtf': True,
                'requires_bank': True,
                'seniat_code': '06',
                'sequence': 6,
            },
            {
                'name': 'Pago Electrónico',
                'code': 'PEL',
                'payment_type': 'electronic',
                'applies_igtf': True,
                'requires_bank': True,
                'seniat_code': '07',
                'sequence': 7,
            },
            {
                'name': 'Divisas USD',
                'code': 'USD',
                'payment_type': 'cash',
                'applies_igtf': False,
                'is_foreign_currency': True,
                'seniat_code': '08',
                'sequence': 8,
            },
            {
                'name': 'Zelle',
                'code': 'ZEL',
                'payment_type': 'electronic',
                'applies_igtf': False,
                'is_foreign_currency': True,
                'seniat_code': '09',
                'sequence': 9,
            },
        ]
        
        created_methods = []
        for method_data in methods_data:
            method_data['company_id'] = company.id
            existing_method = self.search([
                ('code', '=', method_data['code']),
                ('company_id', '=', company.id)
            ], limit=1)
            if not existing_method:
                method = self.create(method_data)
                created_methods.append(method)
        
        return created_methods
    
    def get_igtf_amount(self, base_amount):
        """Calculate IGTF amount for this payment method"""
        self.ensure_one()
        if self.applies_igtf:
            return base_amount * (self.igtf_rate / 100)
        return 0.0
    
    def get_payment_info(self):
        """Get payment method information"""
        self.ensure_one()
        return {
            'name': self.name,
            'code': self.code,
            'type': self.payment_type,
            'applies_igtf': self.applies_igtf,
            'igtf_rate': self.igtf_rate,
            'requires_bank': self.requires_bank,
            'bank_name': self.bank_id.name if self.bank_id else '',
            'currency': self.currency_id.name if self.currency_id else '',
            'is_foreign_currency': self.is_foreign_currency,
            'seniat_code': self.seniat_code or '',
        }


class AccountMove(models.Model):
    _inherit = 'account.move'
    
    # Add payment method to invoices
    payment_method_ids = fields.Many2many(
        'modo.pago',
        string='Métodos de Pago',
        help='Métodos de pago utilizados en esta factura'
    )
    
    def get_payment_methods_info(self):
        """Get information about payment methods used"""
        self.ensure_one()
        methods_info = []
        for method in self.payment_method_ids:
            methods_info.append(method.get_payment_info())
        return methods_info