# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    # Venezuelan payment fields
    payment_method_ve = fields.Many2one(
        'modo.pago',
        string='Método de Pago Venezolano',
        help='Método de pago según normativa venezolana'
    )
    
    # IGTF fields
    applies_igtf = fields.Boolean(
        string='Aplica IGTF',
        compute='_compute_applies_igtf',
        store=True,
        help='Indica si este pago aplica IGTF'
    )
    igtf_amount = fields.Monetary(
        string='Monto IGTF',
        currency_field='currency_id',
        compute='_compute_igtf_amount',
        store=True,
        help='Monto del Impuesto a las Grandes Transacciones Financieras'
    )
    igtf_rate = fields.Float(
        string='Tasa IGTF (%)',
        default=3.0,
        help='Porcentaje de IGTF aplicable'
    )
    
    # Withholding fields
    wh_vat_amount = fields.Monetary(
        string='Retención IVA',
        currency_field='currency_id',
        help='Monto de retención de IVA'
    )
    wh_islr_amount = fields.Monetary(
        string='Retención ISLR',
        currency_field='currency_id',
        help='Monto de retención de ISLR'
    )
    wh_municipal_amount = fields.Monetary(
        string='Retención Municipal',
        currency_field='currency_id',
        help='Monto de retención municipal'
    )
    
    # Venezuelan payment reference
    payment_reference_ve = fields.Char(
        string='Referencia de Pago',
        help='Número de referencia del pago (confirmación, autorización, etc.)'
    )
    
    # Bank information for electronic payments
    bank_account_origin = fields.Char(
        string='Cuenta Origen',
        help='Número de cuenta origen del pago'
    )
    bank_account_destination = fields.Char(
        string='Cuenta Destino',
        help='Número de cuenta destino del pago'
    )
    
    # Foreign currency fields
    foreign_amount = fields.Float(
        string='Monto en Moneda Extranjera',
        digits='Product Price',
        help='Monto del pago en moneda extranjera'
    )
    foreign_currency_id = fields.Many2one(
        'res.currency',
        string='Moneda Extranjera',
        help='Moneda extranjera utilizada en el pago'
    )
    exchange_rate_used = fields.Float(
        string='Tasa de Cambio Utilizada',
        digits=(12, 6),
        help='Tasa de cambio utilizada para la conversión'
    )
    
    @api.depends('payment_method_ve', 'journal_id')
    def _compute_applies_igtf(self):
        """Compute if IGTF applies based on payment method"""
        for payment in self:
            payment.applies_igtf = False
            if payment.payment_method_ve:
                payment.applies_igtf = payment.payment_method_ve.applies_igtf
            elif payment.journal_id:
                payment.applies_igtf = payment.journal_id.applies_igtf
    
    @api.depends('amount', 'applies_igtf', 'igtf_rate')
    def _compute_igtf_amount(self):
        """Compute IGTF amount"""
        for payment in self:
            if payment.applies_igtf and payment.amount:
                payment.igtf_amount = payment.amount * (payment.igtf_rate / 100)
            else:
                payment.igtf_amount = 0.0
    
    @api.onchange('payment_method_ve')
    def _onchange_payment_method_ve(self):
        """Update fields based on Venezuelan payment method"""
        if self.payment_method_ve:
            self.applies_igtf = self.payment_method_ve.applies_igtf
            self.igtf_rate = self.payment_method_ve.igtf_rate
            
            # Set journal if payment method has one
            if self.payment_method_ve.journal_id:
                self.journal_id = self.payment_method_ve.journal_id
            
            # Set currency if payment method has one
            if self.payment_method_ve.currency_id:
                self.foreign_currency_id = self.payment_method_ve.currency_id
    
    @api.onchange('foreign_amount', 'foreign_currency_id', 'exchange_rate_used')
    def _onchange_foreign_currency(self):
        """Calculate amount in company currency"""
        if self.foreign_amount and self.exchange_rate_used:
            self.amount = self.foreign_amount * self.exchange_rate_used
    
    def _create_payment_vals_from_wizard(self, batch_result):
        """Override to include Venezuelan payment data"""
        payment_vals = super()._create_payment_vals_from_wizard(batch_result)
        
        # Add Venezuelan payment fields
        payment_vals.update({
            'payment_method_ve': self.payment_method_ve.id if self.payment_method_ve else False,
            'applies_igtf': self.applies_igtf,
            'igtf_amount': self.igtf_amount,
            'igtf_rate': self.igtf_rate,
            'wh_vat_amount': self.wh_vat_amount,
            'wh_islr_amount': self.wh_islr_amount,
            'wh_municipal_amount': self.wh_municipal_amount,
            'payment_reference_ve': self.payment_reference_ve,
            'bank_account_origin': self.bank_account_origin,
            'bank_account_destination': self.bank_account_destination,
            'foreign_amount': self.foreign_amount,
            'foreign_currency_id': self.foreign_currency_id.id if self.foreign_currency_id else False,
            'exchange_rate_used': self.exchange_rate_used,
        })
        
        return payment_vals
    
    def _create_payment_vals_from_batch(self, batch_result):
        """Override to handle Venezuelan payment creation"""
        payment_vals_list = super()._create_payment_vals_from_batch(batch_result)
        
        # Process withholdings if applicable
        if self.wh_vat_amount or self.wh_islr_amount or self.wh_municipal_amount:
            for payment_vals in payment_vals_list:
                self._add_withholding_entries(payment_vals, batch_result)
        
        # Process IGTF if applicable
        if self.applies_igtf and self.igtf_amount:
            for payment_vals in payment_vals_list:
                self._add_igtf_entries(payment_vals, batch_result)
        
        return payment_vals_list
    
    def _add_withholding_entries(self, payment_vals, batch_result):
        """Add withholding entries to payment"""
        if not payment_vals.get('line_ids'):
            return
        
        company = self.env.company
        
        # Add IVA withholding
        if self.wh_vat_amount:
            wh_account = company.account_wh_vat_id  # Should be configured
            if wh_account:
                payment_vals['line_ids'].append((0, 0, {
                    'account_id': wh_account.id,
                    'debit': self.wh_vat_amount if payment_vals.get('payment_type') == 'outbound' else 0,
                    'credit': self.wh_vat_amount if payment_vals.get('payment_type') == 'inbound' else 0,
                    'name': _('Retención IVA'),
                }))
        
        # Add ISLR withholding
        if self.wh_islr_amount:
            wh_account = company.account_wh_islr_id  # Should be configured
            if wh_account:
                payment_vals['line_ids'].append((0, 0, {
                    'account_id': wh_account.id,
                    'debit': self.wh_islr_amount if payment_vals.get('payment_type') == 'outbound' else 0,
                    'credit': self.wh_islr_amount if payment_vals.get('payment_type') == 'inbound' else 0,
                    'name': _('Retención ISLR'),
                }))
        
        # Add municipal withholding
        if self.wh_municipal_amount:
            wh_account = company.account_wh_municipal_id  # Should be configured
            if wh_account:
                payment_vals['line_ids'].append((0, 0, {
                    'account_id': wh_account.id,
                    'debit': self.wh_municipal_amount if payment_vals.get('payment_type') == 'outbound' else 0,
                    'credit': self.wh_municipal_amount if payment_vals.get('payment_type') == 'inbound' else 0,
                    'name': _('Retención Municipal'),
                }))
    
    def _add_igtf_entries(self, payment_vals, batch_result):
        """Add IGTF entries to payment"""
        if not payment_vals.get('line_ids'):
            return
        
        company = self.env.company
        igtf_account = company.igtf_tax_id.account_id if company.igtf_tax_id else None
        
        if igtf_account:
            payment_vals['line_ids'].append((0, 0, {
                'account_id': igtf_account.id,
                'debit': self.igtf_amount,
                'credit': 0,
                'name': _('IGTF 3%'),
            }))


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    # Venezuelan payment fields (stored in payment)
    payment_method_ve = fields.Many2one(
        'modo.pago',
        string='Método de Pago Venezolano',
        help='Método de pago según normativa venezolana'
    )
    
    applies_igtf = fields.Boolean(
        string='Aplica IGTF',
        help='Indica si este pago aplica IGTF'
    )
    igtf_amount = fields.Monetary(
        string='Monto IGTF',
        currency_field='currency_id',
        help='Monto del IGTF'
    )
    igtf_rate = fields.Float(
        string='Tasa IGTF (%)',
        help='Porcentaje de IGTF aplicable'
    )
    
    wh_vat_amount = fields.Monetary(
        string='Retención IVA',
        currency_field='currency_id'
    )
    wh_islr_amount = fields.Monetary(
        string='Retención ISLR',
        currency_field='currency_id'
    )
    wh_municipal_amount = fields.Monetary(
        string='Retención Municipal',
        currency_field='currency_id'
    )
    
    payment_reference_ve = fields.Char(
        string='Referencia de Pago'
    )
    bank_account_origin = fields.Char(
        string='Cuenta Origen'
    )
    bank_account_destination = fields.Char(
        string='Cuenta Destino'
    )
    
    foreign_amount = fields.Float(
        string='Monto en Moneda Extranjera',
        digits='Product Price'
    )
    foreign_currency_id = fields.Many2one(
        'res.currency',
        string='Moneda Extranjera'
    )
    exchange_rate_used = fields.Float(
        string='Tasa de Cambio Utilizada',
        digits=(12, 6)
    )
    
    def get_venezuelan_payment_info(self):
        """Get Venezuelan payment information for reports"""
        self.ensure_one()
        return {
            'payment_method': self.payment_method_ve.name if self.payment_method_ve else '',
            'reference': self.payment_reference_ve or '',
            'igtf_amount': self.igtf_amount,
            'total_withholdings': self.wh_vat_amount + self.wh_islr_amount + self.wh_municipal_amount,
            'foreign_amount': self.foreign_amount,
            'foreign_currency': self.foreign_currency_id.name if self.foreign_currency_id else '',
            'exchange_rate': self.exchange_rate_used,
        }