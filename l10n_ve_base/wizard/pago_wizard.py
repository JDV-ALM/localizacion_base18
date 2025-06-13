# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PagoWizard(models.TransientModel):
    _name = 'pago.wizard'
    _description = 'Asistente de Pago Venezolano'

    # Payment information
    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente/Proveedor',
        required=True,
        help='Cliente o proveedor del pago'
    )
    
    amount = fields.Float(
        string='Monto',
        required=True,
        digits='Product Price',
        help='Monto del pago'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        required=True,
        default=lambda self: self.env.company.currency_id,
        help='Moneda del pago'
    )
    
    date = fields.Date(
        string='Fecha',
        required=True,
        default=fields.Date.context_today,
        help='Fecha del pago'
    )
    
    # Venezuelan payment method
    payment_method_ve = fields.Many2one(
        'modo.pago',
        string='Método de Pago',
        required=True,
        help='Método de pago venezolano'
    )
    
    # Payment type
    payment_type = fields.Selection([
        ('inbound', 'Pago Recibido'),
        ('outbound', 'Pago Enviado'),
    ], string='Tipo de Pago', required=True, default='inbound')
    
    # Journal
    journal_id = fields.Many2one(
        'account.journal',
        string='Diario',
        required=True,
        domain="[('type', 'in', ['bank', 'cash'])]",
        help='Diario contable para el pago'
    )
    
    # Communication
    communication = fields.Char(
        string='Concepto',
        help='Concepto o referencia del pago'
    )
    
    # IGTF fields
    applies_igtf = fields.Boolean(
        string='Aplica IGTF',
        compute='_compute_applies_igtf',
        store=True,
        help='Indica si este pago aplica IGTF'
    )
    
    igtf_amount = fields.Float(
        string='Monto IGTF',
        compute='_compute_igtf_amount',
        store=True,
        digits='Product Price',
        help='Monto del IGTF calculado'
    )
    
    igtf_rate = fields.Float(
        string='Tasa IGTF (%)',
        default=3.0,
        help='Porcentaje de IGTF'
    )
    
    # Withholding fields
    wh_vat_amount = fields.Float(
        string='Retención IVA',
        digits='Product Price',
        help='Monto de retención de IVA'
    )
    
    wh_islr_amount = fields.Float(
        string='Retención ISLR',
        digits='Product Price',
        help='Monto de retención de ISLR'
    )
    
    wh_municipal_amount = fields.Float(
        string='Retención Municipal',
        digits='Product Price',
        help='Monto de retención municipal'
    )
    
    # Bank information
    bank_reference = fields.Char(
        string='Referencia Bancaria',
        help='Número de referencia bancaria'
    )
    
    account_origin = fields.Char(
        string='Cuenta Origen',
        help='Número de cuenta origen'
    )
    
    account_destination = fields.Char(
        string='Cuenta Destino',
        help='Número de cuenta destino'
    )
    
    # Foreign currency
    foreign_amount = fields.Float(
        string='Monto en Moneda Extranjera',
        digits='Product Price',
        help='Monto en moneda extranjera'
    )
    
    foreign_currency_id = fields.Many2one(
        'res.currency',
        string='Moneda Extranjera',
        help='Moneda extranjera del pago'
    )
    
    exchange_rate = fields.Float(
        string='Tasa de Cambio',
        digits=(12, 6),
        help='Tasa de cambio utilizada'
    )
    
    # Total amount
    total_amount = fields.Float(
        string='Monto Total',
        compute='_compute_total_amount',
        store=True,
        digits='Product Price',
        help='Monto total incluyendo IGTF'
    )
    
    @api.depends('payment_method_ve')
    def _compute_applies_igtf(self):
        """Compute if IGTF applies based on payment method"""
        for wizard in self:
            wizard.applies_igtf = (
                wizard.payment_method_ve and 
                wizard.payment_method_ve.applies_igtf
            )
    
    @api.depends('amount', 'applies_igtf', 'igtf_rate')
    def _compute_igtf_amount(self):
        """Compute IGTF amount"""
        for wizard in self:
            if wizard.applies_igtf and wizard.amount:
                wizard.igtf_amount = wizard.amount * (wizard.igtf_rate / 100)
            else:
                wizard.igtf_amount = 0.0
    
    @api.depends('amount', 'igtf_amount')
    def _compute_total_amount(self):
        """Compute total amount including IGTF"""
        for wizard in self:
            wizard.total_amount = wizard.amount + wizard.igtf_amount
    
    @api.onchange('payment_method_ve')
    def _onchange_payment_method_ve(self):
        """Update fields based on payment method"""
        if self.payment_method_ve:
            self.applies_igtf = self.payment_method_ve.applies_igtf
            self.igtf_rate = self.payment_method_ve.igtf_rate
            
            # Set journal if payment method has one
            if self.payment_method_ve.journal_id:
                self.journal_id = self.payment_method_ve.journal_id
            
            # Set foreign currency if payment method uses it
            if self.payment_method_ve.is_foreign_currency:
                if self.payment_method_ve.currency_id:
                    self.foreign_currency_id = self.payment_method_ve.currency_id
    
    @api.onchange('foreign_amount', 'exchange_rate')
    def _onchange_foreign_currency(self):
        """Calculate amount in company currency"""
        if self.foreign_amount and self.exchange_rate:
            self.amount = self.foreign_amount * self.exchange_rate
    
    @api.onchange('currency_id', 'date')
    def _onchange_currency_date(self):
        """Update exchange rate when currency or date changes"""
        if self.currency_id and self.currency_id != self.env.company.currency_id:
            rate = self.currency_id._get_conversion_rate(
                self.currency_id,
                self.env.company.currency_id,
                self.env.company,
                self.date
            )
            self.exchange_rate = rate
    
    def action_create_payment(self):
        """Create payment from wizard"""
        self.ensure_one()
        
        # Validate required fields
        if not self.amount or self.amount <= 0:
            raise UserError(_('El monto debe ser mayor a cero'))
        
        # Prepare payment values
        payment_vals = {
            'payment_type': self.payment_type,
            'partner_id': self.partner_id.id,
            'amount': self.total_amount,
            'currency_id': self.currency_id.id,
            'date': self.date,
            'journal_id': self.journal_id.id,
            'ref': self.communication,
            'payment_method_line_id': self.journal_id.inbound_payment_method_line_ids[0].id if self.payment_type == 'inbound' else self.journal_id.outbound_payment_method_line_ids[0].id,
        }
        
        # Add Venezuelan specific fields
        payment_vals.update({
            'payment_method_ve': self.payment_method_ve.id,
            'applies_igtf': self.applies_igtf,
            'igtf_amount': self.igtf_amount,
            'igtf_rate': self.igtf_rate,
            'wh_vat_amount': self.wh_vat_amount,
            'wh_islr_amount': self.wh_islr_amount,
            'wh_municipal_amount': self.wh_municipal_amount,
            'payment_reference_ve': self.bank_reference,
            'bank_account_origin': self.account_origin,
            'bank_account_destination': self.account_destination,
            'foreign_amount': self.foreign_amount,
            'foreign_currency_id': self.foreign_currency_id.id if self.foreign_currency_id else False,
            'exchange_rate_used': self.exchange_rate,
        })
        
        # Create payment
        payment = self.env['account.payment'].create(payment_vals)
        
        # Create IGTF entry if applicable
        if self.applies_igtf and self.igtf_amount:
            self._create_igtf_entry(payment)
        
        # Create withholding entries if applicable
        if any([self.wh_vat_amount, self.wh_islr_amount, self.wh_municipal_amount]):
            self._create_withholding_entries(payment)
        
        # Post payment
        payment.action_post()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Pago Creado'),
            'res_model': 'account.payment',
            'res_id': payment.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def _create_igtf_entry(self, payment):
        """Create IGTF accounting entry"""
        if not self.env.company.igtf_tax_id:
            raise UserError(_('No se ha configurado el impuesto IGTF en la compañía'))
        
        igtf_account = self.env.company.igtf_tax_id.account_id
        if not igtf_account:
            raise UserError(_('No se ha configurado la cuenta contable para IGTF'))
        
        # Create additional move line for IGTF
        move_line_vals = {
            'move_id': payment.move_id.id,
            'account_id': igtf_account.id,
            'name': _('IGTF %s%%') % self.igtf_rate,
            'debit': self.igtf_amount if self.payment_type == 'outbound' else 0,
            'credit': self.igtf_amount if self.payment_type == 'inbound' else 0,
        }
        
        self.env['account.move.line'].create(move_line_vals)
    
    def _create_withholding_entries(self, payment):
        """Create withholding accounting entries"""
        company = self.env.company
        
        # IVA withholding
        if self.wh_vat_amount:
            wh_account = company.account_wh_vat_id  # Should be configured
            if wh_account:
                move_line_vals = {
                    'move_id': payment.move_id.id,
                    'account_id': wh_account.id,
                    'name': _('Retención IVA'),
                    'debit': self.wh_vat_amount if self.payment_type == 'inbound' else 0,
                    'credit': self.wh_vat_amount if self.payment_type == 'outbound' else 0,
                }
                self.env['account.move.line'].create(move_line_vals)
        
        # ISLR withholding
        if self.wh_islr_amount:
            wh_account = company.account_wh_islr_id  # Should be configured
            if wh_account:
                move_line_vals = {
                    'move_id': payment.move_id.id,
                    'account_id': wh_account.id,
                    'name': _('Retención ISLR'),
                    'debit': self.wh_islr_amount if self.payment_type == 'inbound' else 0,
                    'credit': self.wh_islr_amount if self.payment_type == 'outbound' else 0,
                }
                self.env['account.move.line'].create(move_line_vals)
        
        # Municipal withholding
        if self.wh_municipal_amount:
            wh_account = company.account_wh_municipal_id  # Should be configured
            if wh_account:
                move_line_vals = {
                    'move_id': payment.move_id.id,
                    'account_id': wh_account.id,
                    'name': _('Retención Municipal'),
                    'debit': self.wh_municipal_amount if self.payment_type == 'inbound' else 0,
                    'credit': self.wh_municipal_amount if self.payment_type == 'outbound' else 0,
                }
                self.env['account.move.line'].create(move_line_vals)